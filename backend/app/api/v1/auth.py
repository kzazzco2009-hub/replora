"""§2 auth endpoints (docs/api_contract.md). Contract stubs: each one answers 501 until Phase 5."""

from uuid import UUID

from fastapi import APIRouter

from app.api.problem import ERROR_RESPONSES, not_implemented
from app.api.v1.auth_models import (
    EmailRequest,
    ExportAccepted,
    ExportStatus,
    LoginRequest,
    Me,
    MfaCodeRequest,
    MfaDisableRequest,
    MfaEnrollment,
    MfaRecoveryRequest,
    MfaRequired,
    PasswordRequest,
    RegisterRequest,
    ResetPasswordRequest,
    Session,
    TokenRequest,
    UpdateMeRequest,
    User,
)

router = APIRouter(prefix="/auth", tags=["auth"], responses=ERROR_RESPONSES)


@router.get("/csrf", status_code=204)
def get_csrf() -> None:
    """Set the readable `replora_csrf` cookie (call at app start when it is missing)."""
    raise not_implemented()


@router.post("/register", status_code=201)
def register(body: RegisterRequest) -> User:
    """Create an account and send the verification email."""
    raise not_implemented()


@router.post("/login")
def login(body: LoginRequest) -> User | MfaRequired:
    """Start a session, or return `mfa_required` with a challenge cookie."""
    raise not_implemented()


@router.post("/logout", status_code=204)
def logout() -> None:
    """Revoke the current session and clear its cookies."""
    raise not_implemented()


@router.post("/refresh", status_code=204)
def refresh() -> None:
    """Rotate the session cookies using the refresh cookie."""
    raise not_implemented()


@router.get("/me")
def get_me() -> Me:
    """The current user with their workspace memberships."""
    raise not_implemented()


@router.patch("/me")
def update_me(body: UpdateMeRequest) -> User:
    """Update the profile: display name, locale, theme, timezone."""
    raise not_implemented()


@router.delete("/me", status_code=202)
def delete_me(body: PasswordRequest) -> None:
    """Schedule account deletion after the grace period."""
    raise not_implemented()


@router.post("/verify-email", status_code=204)
def verify_email(body: TokenRequest) -> None:
    """Confirm the email address with the emailed token."""
    raise not_implemented()


@router.post("/password/forgot", status_code=202)
def forgot_password(body: EmailRequest) -> None:
    """Send a reset email if the account exists. Always 202 (no enumeration)."""
    raise not_implemented()


@router.post("/password/reset", status_code=204)
def reset_password(body: ResetPasswordRequest) -> None:
    """Set a new password with the emailed token."""
    raise not_implemented()


@router.post("/mfa/enroll")
def enroll_mfa() -> MfaEnrollment:
    """Start TOTP enrollment. MFA is not active until confirmed."""
    raise not_implemented()


@router.post("/mfa/enroll/confirm", status_code=204)
def confirm_mfa(body: MfaCodeRequest) -> None:
    """Activate MFA with a code from the authenticator app."""
    raise not_implemented()


@router.post("/mfa/challenge")
def mfa_challenge(body: MfaCodeRequest | MfaRecoveryRequest) -> User:
    """Finish an MFA login with a TOTP code or a recovery code (uses the challenge cookie)."""
    raise not_implemented()


@router.delete("/mfa", status_code=204)
def disable_mfa(body: MfaDisableRequest) -> None:
    """Turn MFA off (needs the password and a current code)."""
    raise not_implemented()


@router.post("/me/export", status_code=202)
def start_export() -> ExportAccepted:
    """Start an export of the user's data."""
    raise not_implemented()


@router.get("/me/export/{export_id}")
def get_export(export_id: UUID) -> ExportStatus:
    """Poll an export; `url` is set when it is ready."""
    raise not_implemented()


@router.get("/sessions")
def list_sessions() -> list[Session]:
    """The current user's active sessions."""
    raise not_implemented()


@router.delete("/sessions/{session_id}", status_code=204)
def revoke_session(session_id: UUID) -> None:
    """Revoke a session. Revoking the current one also clears its cookies."""
    raise not_implemented()
