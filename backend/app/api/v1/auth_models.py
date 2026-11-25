"""Request and response bodies for §2 auth (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import EmailStr, Field

from app.api.models import ApiModel
from app.api.v1.workspace_models import Workspace

Locale = Literal["ar", "en"]
Theme = Literal["light", "dark", "system"]
Password = Annotated[str, Field(min_length=12, max_length=256)]
CurrentPassword = Annotated[str, Field(min_length=1, max_length=256)]
OtpCode = Annotated[str, Field(pattern=r"^\d{6}$")]


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
    email: EmailStr
    password: Password
    display_name: Annotated[str, Field(min_length=1, max_length=100)]
    locale: Locale


class LoginRequest(ApiModel):
    email: EmailStr
    password: CurrentPassword


class UpdateMeRequest(ApiModel):
    display_name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    locale: Locale | None = None
    theme: Theme | None = None
    timezone: str | None = Field(default=None, description="IANA name, e.g. Africa/Cairo")


class TokenRequest(ApiModel):
    token: str


class EmailRequest(ApiModel):
    email: EmailStr


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


class MfaRecoveryRequest(ApiModel):
    recovery_code: str


class MfaDisableRequest(ApiModel):
    password: CurrentPassword
    code: OtpCode


class ExportAccepted(ApiModel):
    export_id: UUID


class ExportStatus(ApiModel):
    status: Literal["pending", "ready", "failed"]
    url: str | None = None
