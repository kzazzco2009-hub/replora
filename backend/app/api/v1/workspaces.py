"""§3 workspaces, members, invitations and audit (docs/api_contract.md). 501 stubs until Phase 5."""

from uuid import UUID

from fastapi import APIRouter

from app.api.models import Cursor, Limit
from app.api.problem import ERROR_RESPONSES, NOT_FOUND_RESPONSE, not_implemented
from app.api.v1.auth_models import TokenRequest
from app.api.v1.workspace_models import (
    AuditEventPage,
    CreateWorkspaceRequest,
    Invitation,
    InvitationRequest,
    Member,
    UpdateMemberRequest,
    Workspace,
)

router = APIRouter(tags=["workspaces"], responses=ERROR_RESPONSES)
scoped = APIRouter(prefix="/workspaces/{ws_id}", responses=NOT_FOUND_RESPONSE)


@router.get("/workspaces", name="list")
def list_workspaces() -> list[Workspace]:
    """The workspaces the current user belongs to."""
    raise not_implemented()


@router.post("/workspaces", status_code=201, name="create")
def create_workspace(body: CreateWorkspaceRequest) -> Workspace:
    """Create a workspace owned by the current user."""
    raise not_implemented()


@scoped.delete("", status_code=204, name="delete")
def delete_workspace(ws_id: UUID) -> None:
    """Delete the workspace with its files, runs and workflows (owner only).

    The personal workspace cannot be deleted: 409 `PERSONAL_WORKSPACE_UNDELETABLE`.
    """
    raise not_implemented()


@scoped.get("/members")
def list_members(ws_id: UUID) -> list[Member]:
    """The workspace members (any member)."""
    raise not_implemented()


@scoped.patch("/members/{user_id}")
def update_member(ws_id: UUID, user_id: UUID, body: UpdateMemberRequest) -> Member:
    """Change a member's role (members.manage)."""
    raise not_implemented()


@scoped.delete("/members/{user_id}", status_code=204)
def remove_member(ws_id: UUID, user_id: UUID) -> None:
    """Remove a member (members.manage)."""
    raise not_implemented()


@scoped.post("/invitations", status_code=201)
def invite(ws_id: UUID, body: InvitationRequest) -> Invitation:
    """Invite by email. The role cannot be above the inviter's (members.manage)."""
    raise not_implemented()


@scoped.get("/invitations")
def list_invitations(ws_id: UUID) -> list[Invitation]:
    """The workspace invitations (members.manage)."""
    raise not_implemented()


@scoped.delete("/invitations/{invitation_id}", status_code=204)
def revoke_invitation(ws_id: UUID, invitation_id: UUID) -> None:
    """Revoke a pending invitation (members.manage)."""
    raise not_implemented()


@router.post("/invitations/accept")
def accept_invitation(body: TokenRequest) -> Workspace:
    """Join the workspace with the emailed token. The signed-in email must match the invitation."""
    raise not_implemented()


@scoped.get("/audit")
def list_audit(ws_id: UUID, cursor: Cursor = None, limit: Limit = 25) -> AuditEventPage:
    """The workspace audit log, newest first (audit.read)."""
    raise not_implemented()


router.include_router(scoped)
