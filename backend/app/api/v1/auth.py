"""§2 auth endpoints (docs/api_contract.md). Contract stubs: each one answers 501 until Phase 5."""

from typing import Annotated
from uuid import UUID, uuid7

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select

from app.api.csrf import issue_csrf
from app.api.problem import (
    ERROR_RESPONSES,
    NOT_FOUND_RESPONSE,
    WRONG_SECRET_RESPONSE,
    ProblemError,
    not_implemented,
)
from app.api.session import (
    REFRESH_COOKIE,
    Caller,
    caller,
    clear_session_cookies,
    database,
    now,
    set_session_cookies,
    unauthenticated,
)
from app.api.v1.auth_models import (
    EmailRequest,
    ExportAccepted,
    ExportStatus,
    LoginRequest,
    Me,
    MfaChallengeRequest,
    MfaCodeRequest,
    MfaDisableRequest,
    MfaEnrollment,
    MfaRequired,
    PasswordRequest,
    RegisterRequest,
    ResetPasswordRequest,
    Session,
    TokenRequest,
    UpdateMeRequest,
    User,
)
from app.api.v1.workspace_models import Workspace
from app.auth import accounts, audit, limits, one_time, privacy, sessions
from app.auth.mail import compose
from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import digest
from app.db import models as m

router = APIRouter(prefix="/auth", tags=["auth"], responses=ERROR_RESPONSES)


@router.get("/csrf", status_code=204)
def get_csrf(request: Request, response: Response) -> None:
    """Set the readable `replora_csrf` cookie (call at app start when it is missing)."""
    issue_csrf(request, response)


@router.post("/register", status_code=202)
def register(body: RegisterRequest, request: Request) -> None:
    """Always 202 with no body (no enumeration, S‑26).

    A new address gets the verification email; an existing account gets a notice email instead.
    """
    ip = client_ip(request)
    with database(request).begin() as session:
        if (limited := limits.over(session, limits.REGISTER, [ip], now(request))) is None:
            limits.hit(session, limits.REGISTER, ip, now(request))
            user, created = accounts.register(
                session, body.email, body.password, body.display_name, body.locale
            )
            audit.record(session, "auth.register", user.id, ip_hash=ip)
    if limited is not None:
        raise limited
    with database(request).begin() as session:
        if created:
            token = one_time.issue(session, user, "verify", now(request))
            message = compose(
                user.email, "verify", user.locale, link(request, "verify-email", token)
            )
        else:
            message = compose(user.email, "account_exists", user.locale)
    request.app.state.mailer.send(message)
    return Response(status_code=202)  # type: ignore[return-value]  (no body at all, not `null`)


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response) -> User | MfaRequired:
    """Start a session, or return `mfa_required` with a challenge cookie."""
    ip, account = client_ip(request), digest(accounts.normal_email(body.email))
    with database(request).begin() as session:
        limited = limits.over(session, limits.LOGIN, [ip, account], now(request))
        user = None if limited else accounts.authenticate(session, body.email, body.password)
        if limited is None and user is None:
            for subject in (ip, account):
                limits.hit(session, limits.LOGIN, subject, now(request))
            known = accounts.find_user(session, body.email)
            audit.record(session, "auth.login_failed", known.id if known else None, ip_hash=ip)
        if user is not None:
            agent = request.headers.get("user-agent")
            row, refresh_token = sessions.start(session, user.id, now(request), user_agent=agent,
                                                ip_hash=ip)  # fmt: skip
            audit.record(session, "auth.login", user.id, ip_hash=ip)
    if limited is not None:
        raise limited
    if user is None:
        raise ProblemError(401, "INVALID_CREDENTIALS", "Invalid credentials")
    set_session_cookies(request, response, row, refresh_token)
    issue_csrf(request, response)
    return to_user(user)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    """Revoke the current session and clear its cookies."""
    try:
        signed_in = caller(request)
    except ProblemError:
        signed_in = None
    if signed_in is not None:
        with database(request).begin() as session:
            sessions.revoke(session, signed_in.session_id, now(request))
            audit.record(session, "auth.logout", signed_in.user.id, ip_hash=client_ip(request))
    clear_session_cookies(response)
    issue_csrf(request, response)


@router.post("/refresh", status_code=204)
def refresh(request: Request, response: Response) -> None:
    """Rotate the session cookies using the refresh cookie."""
    with database(request).begin() as session:
        rotated = sessions.rotate(session, request.cookies.get(REFRESH_COOKIE, ""), now(request))
    if rotated is None:
        raise unauthenticated()
    set_session_cookies(request, response, *rotated)


@router.get("/me")
def get_me(signed_in: Annotated[Caller, Depends(caller)], request: Request) -> Me:
    """The current user with their workspace memberships."""
    with database(request)() as session:
        rows = session.execute(
            select(m.Workspace, m.Membership.role)
            .join(m.Membership, m.Membership.workspace_id == m.Workspace.id)
            .where(m.Membership.user_id == signed_in.user.id)
            .order_by(m.Workspace.created_at)
        ).all()
    memberships = [Workspace(id=w.id, name=w.name, role=role, created_at=w.created_at)
                   for w, role in rows]  # fmt: skip
    return Me(**to_user(signed_in.user).model_dump(), memberships=memberships)


@router.patch("/me")
def update_me(body: UpdateMeRequest, request: Request) -> User:
    """Update the profile: display name, locale, theme, timezone."""
    with database(request).begin() as session:
        user = session.get(m.User, request.state.caller.user.id)
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(user, field, value)
    return to_user(user)


@router.delete("/me", status_code=202, responses=WRONG_SECRET_RESPONSE)
def delete_me(body: PasswordRequest, request: Request, response: Response) -> None:
    """Schedule account deletion after the grace period."""
    with database(request).begin() as session:
        user = session.get(m.User, request.state.caller.user.id)
        if not verify_password(body.password, user.password_hash)[0]:
            raise ProblemError(400, "PASSWORD_INCORRECT", "Wrong password")
        privacy.request_deletion(session, user, now(request))
        audit.record(session, "auth.deletion_requested", user.id, ip_hash=client_ip(request))
    clear_session_cookies(response)
    response.status_code = 202


@router.post("/verify-email", status_code=204, responses=WRONG_SECRET_RESPONSE)
def verify_email(body: TokenRequest, request: Request) -> None:
    """Confirm the email address with the emailed token."""
    with database(request).begin() as session:
        user = one_time.redeem(session, "verify", body.token, now(request))
        if user is None:
            raise token_invalid()
        user.email_verified_at = now(request)


@router.post("/password/forgot", status_code=202)
def forgot_password(body: EmailRequest, request: Request) -> None:
    """Send a reset email if the account exists. Always 202 (no enumeration)."""
    ip, message = client_ip(request), None
    with database(request).begin() as session:
        if (limited := limits.over(session, limits.FORGOT, [ip], now(request))) is None:
            limits.hit(session, limits.FORGOT, ip, now(request))
            user = accounts.find_user(session, body.email)
            if user is not None and user.deleted_at is None:
                token = one_time.issue(session, user, "reset", now(request))
                page = link(request, "reset-password", token)
                message = compose(user.email, "reset", user.locale, page)
    if limited is not None:
        raise limited
    if message is not None:
        request.app.state.mailer.send(message)
    return Response(status_code=202)  # type: ignore[return-value]


@router.post("/password/reset", status_code=204, responses=WRONG_SECRET_RESPONSE)
def reset_password(body: ResetPasswordRequest, request: Request) -> None:
    """Set a new password with the emailed token."""
    # S‑27: a new password signs every session out.
    with database(request).begin() as session:
        user = one_time.redeem(session, "reset", body.token, now(request))
        if user is None:
            raise token_invalid()
        user.password_hash = hash_password(body.password)
        one_time.revoke_all_sessions(session, user, now(request))
        audit.record(session, "auth.password_reset", user.id, ip_hash=client_ip(request))


@router.post("/mfa/enroll")
def enroll_mfa() -> MfaEnrollment:
    """Start TOTP enrollment. MFA is not active until confirmed."""
    raise not_implemented()


@router.post("/mfa/enroll/confirm", status_code=204, responses=WRONG_SECRET_RESPONSE)
def confirm_mfa(body: MfaCodeRequest) -> None:
    """Activate MFA with a code from the authenticator app."""
    raise not_implemented()


@router.post("/mfa/challenge", responses=WRONG_SECRET_RESPONSE)
def mfa_challenge(body: MfaChallengeRequest) -> User:
    """Finish an MFA login with a TOTP code or a recovery code (uses the challenge cookie)."""
    raise not_implemented()


@router.delete("/mfa", status_code=204, responses=WRONG_SECRET_RESPONSE)
def disable_mfa(body: MfaDisableRequest) -> None:
    """Turn MFA off (needs the password and a current code)."""
    raise not_implemented()


@router.post("/me/export", status_code=202)
def start_export(request: Request) -> ExportAccepted:
    """Start an export of the user's data."""
    user, export_id = request.state.caller.user, uuid7()
    with database(request)() as session:
        data = privacy.export_archive(session, session.get(m.User, user.id))
    path = privacy.archive_path(request.app.state.settings, user.id, export_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return ExportAccepted(export_id=export_id)


@router.get("/me/export/{export_id}", responses=NOT_FOUND_RESPONSE)
def get_export(export_id: UUID, request: Request) -> ExportStatus:
    """Poll an export; `url` is set when it is ready."""
    path = privacy.archive_path(request.app.state.settings, request.state.caller.user.id, export_id)
    if not path.exists():
        raise ProblemError(404, "NOT_FOUND", "Not found")
    # The signed download URL comes with storage (Phase 6); until then the archive is local.
    return ExportStatus(status="ready")


@router.get("/sessions")
def list_sessions(request: Request) -> list[Session]:
    """The current user's active sessions."""
    signed_in, at = request.state.caller, now(request)
    with database(request)() as session:
        rows = session.scalars(
            select(m.Session)
            .where(m.Session.user_id == signed_in.user.id, m.Session.revoked_at.is_(None),
                   m.Session.expires_at > at)
            .order_by(m.Session.created_at)
        ).all()  # fmt: skip
    return [Session(id=row.id, user_agent=row.user_agent, created_at=row.created_at,
                    expires_at=row.expires_at, current=row.id == signed_in.session_id)
            for row in rows]  # fmt: skip


@router.delete("/sessions/{session_id}", status_code=204, responses=NOT_FOUND_RESPONSE)
def revoke_session(session_id: UUID, request: Request, response: Response) -> None:
    """Revoke a session. Revoking the current one also clears its cookies."""
    signed_in = request.state.caller
    with database(request).begin() as session:
        row = session.get(m.Session, session_id)
        if row is None or row.user_id != signed_in.user.id or row.revoked_at is not None:
            raise ProblemError(404, "NOT_FOUND", "Not found")
        sessions.revoke(session, session_id, now(request))
    if session_id == signed_in.session_id:
        clear_session_cookies(response)


def to_user(row: m.User) -> User:
    return User(id=row.id, email=row.email, display_name=row.display_name, locale=row.locale,
                theme=row.theme, timezone=row.timezone, mfa_enabled=row.mfa_secret_enc is not None,
                email_verified=row.email_verified_at is not None,
                created_at=row.created_at)  # fmt: skip


def token_invalid() -> ProblemError:
    return ProblemError(400, "TOKEN_INVALID", "Invalid or expired token")


def link(request: Request, page: str, token: str) -> str:
    return f"{request.app.state.settings.app_url}/{page}?token={token}"


def client_ip(request: Request) -> str:
    """The caller's IP as an HMAC: it can be counted and compared, never read back."""
    host = request.client.host if request.client else "unknown"
    return limits.ip_hash(host, request.app.state.jwt_key)
