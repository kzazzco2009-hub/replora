"""Every table, imported so `Base.metadata` is complete for Alembic and the tests."""

from app.db.models.identity import (
    AuditEvent,
    AuthToken,
    Invitation,
    Membership,
    MfaRecoveryCode,
    RateLimit,
    Session,
    User,
    Workspace,
)

__all__ = [
    "AuditEvent",
    "AuthToken",
    "Invitation",
    "Membership",
    "MfaRecoveryCode",
    "RateLimit",
    "Session",
    "User",
    "Workspace",
]
