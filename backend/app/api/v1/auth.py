"""§2 auth endpoints (docs/api_contract.md). Contract stubs: each one answers 501 until Phase 5."""

from typing import Annotated
from uuid import UUID

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
from app.auth import accounts, one_time, sessions
from app.auth.mail import compose
from app.auth.passwords import hash_password
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
    with database(request).begin() as session:
        user, created = accounts.register(
            session, body.email, body.password, body.display_name, body.locale
        )
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
    with database(request).begin() as session:
        user = accounts.authenticate(session, body.email, body.password)
        if user is None:
            raise ProblemError(401, "INVALID_CREDENTIALS", "Invalid credentials")
        agent = request.headers.get("user-agent")
        row, refresh_token = sessions.start(session, user.id, now(request), user_agent=agent)
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
def update_me(body: UpdateMeRequest) -> User:
    """Update the profile: display name, locale, theme, timezone."""
    raise not_implemented()


@router.delete("/me", status_code=202, responses=WRONG_SECRET_RESPONSE)
def delete_me(body: PasswordRequest) -> None:
    """Schedule account deletion after the grace period."""
    raise not_implemented()


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
    with database(request).begin() as session:
        user = accounts.find_user(session, body.email)
        if user is None or user.deleted_at is not None:
            return Response(status_code=202)  # type: ignore[return-value]
        token = one_time.issue(session, user, "reset", now(request))
        message = compose(user.email, "reset", user.locale, link(request, "reset-password", token))
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
def start_export() -> ExportAccepted:
    """Start an export of the user's data."""
    raise not_implemented()


@router.get("/me/export/{export_id}", responses=NOT_FOUND_RESPONSE)
def get_export(export_id: UUID) -> ExportStatus:
    """Poll an export; `url` is set when it is ready."""
    raise not_implemented()


@router.get("/sessions")
def list_sessions() -> list[Session]:
    """The current user's active sessions."""
    raise not_implemented()


@router.delete("/sessions/{session_id}", status_code=204, responses=NOT_FOUND_RESPONSE)
def revoke_session(session_id: UUID) -> None:
    """Revoke a session. Revoking the current one also clears its cookies."""
    raise not_implemented()


def to_user(row: m.User) -> User:
    return User(id=row.id, email=row.email, display_name=row.display_name, locale=row.locale,
                theme=row.theme, timezone=row.timezone, mfa_enabled=row.mfa_secret_enc is not None,
                email_verified=row.email_verified_at is not None,
                created_at=row.created_at)  # fmt: skip


def token_invalid() -> ProblemError:
    return ProblemError(400, "TOKEN_INVALID", "Invalid or expired token")


def link(request: Request, page: str, token: str) -> str:
    return f"{request.app.state.settings.app_url}/{page}?token={token}"
