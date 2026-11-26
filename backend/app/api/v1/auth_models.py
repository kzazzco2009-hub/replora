"""Request and response bodies for §2 auth (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AfterValidator, EmailStr, Field, model_validator
from pydantic_core import PydanticCustomError

from app.api.models import ApiModel, Email
from app.api.v1.workspace_models import Workspace
from app.auth.passwords import is_breached

Locale = Literal["ar", "en"]
Theme = Literal["light", "dark", "system"]


def _not_breached(password: str) -> str:
    """P5.1: a password from the breached list is refused (NIST 800-63B)."""
    if is_breached(password):
        raise PydanticCustomError("password_breached", "This password is known from breaches")
    return password


Password = Annotated[str, Field(min_length=12, max_length=256), AfterValidator(_not_breached)]
CurrentPassword = Annotated[str, Field(min_length=1, max_length=256)]
OtpCode = Annotated[str, Field(pattern=r"^\d{6}$")]
RecoveryCode = Annotated[str, Field(min_length=1, max_length=64)]


class User(ApiModel):
    id: UUID
    email: EmailStr
    display_name: str
    locale: Locale
    theme: Theme
    timezone: str = Field(description="IANA name, e.g. Africa/Cairo")
    mfa_enabled: bool
    email_verified: bool
    created_at: datetime


class Me(User):
    memberships: list[Workspace]


class MfaRequired(ApiModel):
    """Login succeeded, but the MFA challenge (`/auth/mfa/challenge`) must be passed first."""

    mfa_required: Literal[True]


class Session(ApiModel):
    id: UUID
    user_agent: str | None
    created_at: datetime
    expires_at: datetime
    current: bool


class RegisterRequest(ApiModel):
    email: Email
    password: Password
    display_name: Annotated[str, Field(min_length=1, max_length=100)]
    locale: Locale


class LoginRequest(ApiModel):
    email: Email
    password: CurrentPassword


class UpdateMeRequest(ApiModel):
    display_name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    locale: Locale | None = None
    theme: Theme | None = None
    timezone: str | None = Field(default=None, description="IANA name, e.g. Africa/Cairo")


class TokenRequest(ApiModel):
    token: str


class EmailRequest(ApiModel):
    email: Email


class ResetPasswordRequest(ApiModel):
    token: str
    password: Password


class PasswordRequest(ApiModel):
    password: CurrentPassword


class MfaEnrollment(ApiModel):
    """Shown once. MFA becomes active only after `/auth/mfa/enroll/confirm`."""

    otpauth_uri: str
    recovery_codes: list[str]


class MfaCodeRequest(ApiModel):
    code: OtpCode


class MfaChallengeRequest(ApiModel):
    """Exactly one of `code` (TOTP) or `recovery_code`."""

    code: OtpCode | None = None
    recovery_code: RecoveryCode | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> Self:
        if (self.code is None) == (self.recovery_code is None):
            raise PydanticCustomError(
                "mfa_code_or_recovery_required", "Send exactly one of code or recovery_code"
            )
        return self


class MfaDisableRequest(ApiModel):
    password: CurrentPassword
    code: OtpCode


class ExportAccepted(ApiModel):
    export_id: UUID


class ExportStatus(ApiModel):
    status: Literal["pending", "ready", "failed"]
    url: str | None = None
