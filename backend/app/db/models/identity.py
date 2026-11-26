"""Users, workspaces and the auth tables (P4.2). The indexes are the ones in `plan.md` §6."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Index, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedMixin, IdMixin


class User(IdMixin, CreatedMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_created_at", "created_at"),
        Index("ix_users_deleted_at", "deleted_at"),
    )

    email: Mapped[str] = mapped_column(String(320))
    display_name: Mapped[str] = mapped_column(String(100), default="", server_default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    email_verified_at: Mapped[datetime | None]
    locale: Mapped[str] = mapped_column(String(8), default="ar")
    theme: Mapped[str] = mapped_column(String(8), default="system")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    mfa_secret_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    deleted_at: Mapped[datetime | None]


Index("uq_users_email", func.lower(User.email), unique=True)
"""Emails are unique ignoring case (T4.7)."""


class Workspace(IdMixin, CreatedMixin, Base):
    __tablename__ = "workspaces"
    __table_args__ = (Index("ix_workspaces_owner_id", "owner_id"),)

    name: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    personal: Mapped[bool] = mapped_column(default=False)


class Membership(IdMixin, CreatedMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (
        Index("uq_memberships_ws_user", "workspace_id", "user_id", unique=True),
        Index("ix_memberships_user_id", "user_id"),
    )

    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(16))


class Session(IdMixin, CreatedMixin, Base):
    """One login. The refresh token is stored only as its SHA-256 (S-24)."""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("uq_sessions_refresh_hash", "refresh_hash", unique=True),
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_expires_at", "expires_at"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    refresh_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_hash: Mapped[str | None] = mapped_column(String(64))


class UsedRefreshToken(IdMixin, Base):
    """A refresh token already rotated away. Seeing it again means the session leaked (S-24)."""

    __tablename__ = "used_refresh_tokens"
    __table_args__ = (
        Index("uq_used_refresh_hash", "token_hash", unique=True),
        Index("ix_used_refresh_session_id", "session_id"),
    )

    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64))
    used_at: Mapped[datetime]


class AuthToken(IdMixin, CreatedMixin, Base):
    """An email-verification or password-reset token, stored hashed and used once (S-27)."""

    __tablename__ = "auth_tokens"
    __table_args__ = (
        Index("uq_auth_tokens_hash", "token_hash", unique=True),
        Index("ix_auth_tokens_user_kind", "user_id", "kind"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]


class Invitation(IdMixin, CreatedMixin, Base):
    __tablename__ = "invitations"
    __table_args__ = (
        Index("uq_invitations_token_hash", "token_hash", unique=True),
        Index("ix_invitations_ws_email", "workspace_id", "email"),
        Index("ix_invitations_expires_at", "expires_at"),
        Index("ix_invitations_invited_by", "invited_by"),
    )

    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(320))
    role: Mapped[str] = mapped_column(String(16))
    token_hash: Mapped[str] = mapped_column(String(64))
    invited_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    expires_at: Mapped[datetime]
    accepted_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]


class MfaRecoveryCode(IdMixin, CreatedMixin, Base):
    __tablename__ = "mfa_recovery_codes"
    __table_args__ = (Index("ix_mfa_recovery_user_id", "user_id"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    code_hash: Mapped[str] = mapped_column(String(255))
    used_at: Mapped[datetime | None]


class AuditEvent(IdMixin, CreatedMixin, Base):
    """Kept after a user is deleted: the actor becomes NULL (anonymized, S-29)."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_ws_created", "workspace_id", "created_at"),
        Index("ix_audit_actor_created", "actor_id", "created_at"),
        Index("ix_audit_target", "target_type", "target_id"),
    )

    workspace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL")
    )
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[str | None] = mapped_column(String(64))
    ip_hash: Mapped[str | None] = mapped_column(String(64))


class RateLimit(Base):
    """A fixed-window counter per key, for example `login:<account hash>` (S-26)."""

    __tablename__ = "rate_limits"
    __table_args__ = (Index("ix_rate_limits_window_start", "window_start"),)

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(primary_key=True)
    count: Mapped[int] = mapped_column(default=0)
