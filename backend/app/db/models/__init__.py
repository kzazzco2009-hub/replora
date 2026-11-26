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
from app.db.models.work import (
    Artifact,
    Draft,
    File,
    Job,
    Run,
    RunEvent,
    RunNode,
    Workflow,
    WorkflowVersion,
)

__all__ = [
    "Artifact",
    "AuditEvent",
    "AuthToken",
    "Draft",
    "File",
    "Invitation",
    "Job",
    "Membership",
    "MfaRecoveryCode",
    "RateLimit",
    "Run",
    "RunEvent",
    "RunNode",
    "Session",
    "User",
    "Workflow",
    "WorkflowVersion",
    "Workspace",
]
