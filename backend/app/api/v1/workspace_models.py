"""Request and response bodies for §3 workspaces and members (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import EmailStr, Field

from app.api.models import ApiModel, Email, Page

Role = Literal["owner", "admin", "member", "viewer"]
GrantableRole = Literal["admin", "member", "viewer"]
"""A role that can be given by invitation or role change; there is one owner (S‑23, S‑29)."""


class Workspace(ApiModel):
    """A workspace the current user belongs to, with their role in it."""

    id: UUID
    name: str
    role: Role
    created_at: datetime


class CreateWorkspaceRequest(ApiModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]


class Member(ApiModel):
    user_id: UUID
    email: EmailStr
    display_name: str
    role: Role


class UpdateMemberRequest(ApiModel):
    role: GrantableRole


class Invitation(ApiModel):
    id: UUID
    email: EmailStr
    role: GrantableRole
    invited_by: UUID
    expires_at: datetime
    status: Literal["pending", "accepted", "revoked", "expired"]


class InvitationRequest(ApiModel):
    email: Email
    role: GrantableRole


AuditAction = Literal[
    "workspace.created",
    "member.invited",
    "member.invitation_revoked",
    "member.joined",
    "member.role_changed",
    "member.removed",
    "file.uploaded",
    "file.downloaded",
    "file.deleted",
    "workflow.saved",
    "workflow.deleted",
    "run.created",
    "run.approved",
    "run.cancelled",
    "output.downloaded",
    "planner.called",
]
"""Workspace audit actions (S‑52). Auth events have no workspace and are not listed here."""
AuditTargetType = Literal[
    "workspace", "invitation", "member", "file", "workflow", "draft", "run", "output"
]


class AuditEvent(ApiModel):
    id: UUID
    actor_id: UUID | None = Field(description="`null` once the actor's account is deleted (S‑29)")
    action: AuditAction
    target_type: AuditTargetType
    target_id: UUID
    created_at: datetime


class AuditEventPage(Page[AuditEvent]):
    pass
