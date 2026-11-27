"""§3 workspaces, members, invitations and audit (docs/api_contract.md). 501 stubs until Phase 5."""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.models import Cursor, Limit
from app.api.problem import ERROR_RESPONSES, NOT_FOUND_RESPONSE, ProblemError, not_implemented
from app.api.session import database, now
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
from app.auth import audit
from app.auth.access import not_found
from app.auth.accounts import normal_email
from app.auth.mail import compose
from app.auth.permissions import Rank, Role
from app.auth.tokens import digest, new_secret
from app.db import models as m

INVITE_TTL = timedelta(days=7)

router = APIRouter(tags=["workspaces"], responses=ERROR_RESPONSES)
scoped = APIRouter(prefix="/workspaces/{ws_id}", responses=NOT_FOUND_RESPONSE)


@router.get("/workspaces", name="list")
def list_workspaces(request: Request) -> list[Workspace]:
    """The workspaces the current user belongs to."""
    with database(request)() as session:
        return [Workspace(id=w.id, name=w.name, role=role, created_at=w.created_at)
                for w, role in memberships(session, request.state.caller.user.id)]  # fmt: skip


@router.post("/workspaces", status_code=201, name="create")
def create_workspace(body: CreateWorkspaceRequest, request: Request) -> Workspace:
    """Create a workspace owned by the current user."""
    user = request.state.caller.user
    with database(request).begin() as session:
        space = m.Workspace(name=body.name, owner_id=user.id)
        session.add(space)
        session.flush()
        session.add(m.Membership(workspace_id=space.id, user_id=user.id, role="owner"))
        audit.record(session, "workspace.created", user.id, workspace_id=space.id,
                     target_type="workspace", target_id=str(space.id))  # fmt: skip
    return Workspace(id=space.id, name=space.name, role="owner", created_at=space.created_at)


@scoped.delete("", status_code=204, name="delete")
def delete_workspace(ws_id: UUID, request: Request) -> None:
    """Delete the workspace with its files, runs and workflows (owner only).

    The personal workspace cannot be deleted: 409 `PERSONAL_WORKSPACE_UNDELETABLE`.
    """
    with database(request).begin() as session:
        space = session.get(m.Workspace, ws_id)
        if space.personal:
            raise ProblemError(409, "PERSONAL_WORKSPACE_UNDELETABLE", "Personal workspace")
        session.delete(space)


@scoped.get("/members")
def list_members(ws_id: UUID, request: Request) -> list[Member]:
    """The workspace members (any member)."""
    with database(request)() as session:
        rows = session.execute(
            select(m.User, m.Membership.role)
            .join(m.Membership, m.Membership.user_id == m.User.id)
            .where(m.Membership.workspace_id == ws_id)
            .order_by(m.Membership.created_at)
        ).all()
    return [Member(user_id=u.id, email=u.email, display_name=u.display_name, role=role)
            for u, role in rows]  # fmt: skip


@scoped.patch("/members/{user_id}")
def update_member(
    ws_id: UUID, user_id: UUID, body: UpdateMemberRequest, request: Request
) -> Member:
    """Change a member's role (members.manage)."""
    with database(request).begin() as session:
        target, user = _manageable(session, request, ws_id, user_id, grant=body.role)
        target.role = body.role
        audit.record(session, "member.role_changed", request.state.caller.user.id,
                     workspace_id=ws_id, target_type="member", target_id=str(user_id))  # fmt: skip
    return Member(user_id=user.id, email=user.email, display_name=user.display_name,
                  role=body.role)  # fmt: skip


@scoped.delete("/members/{user_id}", status_code=204)
def remove_member(ws_id: UUID, user_id: UUID, request: Request) -> None:
    """Remove a member (members.manage)."""
    with database(request).begin() as session:
        target, _ = _manageable(session, request, ws_id, user_id)
        session.delete(target)
        audit.record(session, "member.removed", request.state.caller.user.id,
                     workspace_id=ws_id, target_type="member", target_id=str(user_id))  # fmt: skip


def _manageable(session, request: Request, ws_id: UUID, user_id: UUID, grant: str | None = None):
    """The member's row and user, if the caller may change them (S-23, S-29).

    The owner can't be changed or removed. Others manage only members ranked below them, and
    never grant a role above their own.
    """
    query = select(m.Membership).where(
        m.Membership.workspace_id == ws_id, m.Membership.user_id == user_id
    )
    target = session.scalars(query).one_or_none()
    if target is None:
        raise not_found()
    mine = Rank[request.state.role.name]
    theirs = Rank[Role(target.role).name]
    granted = Rank[Role(grant).name] if grant else Rank.VIEWER
    if theirs == Rank.OWNER or (mine != Rank.OWNER and (theirs >= mine or granted > mine)):
        raise ProblemError(403, "PERMISSION_DENIED", "Not allowed in this workspace")
    return target, session.get(m.User, user_id)


@scoped.post("/invitations", status_code=201)
def invite(ws_id: UUID, body: InvitationRequest, request: Request) -> Invitation:
    """Invite by email. The role cannot be above the inviter's (members.manage)."""
    # S‑29 holds by structure: only owners and admins hold members.manage, and the body can't
    # ask for more than admin (GrantableRole). A test pins both facts.
    actor, at = request.state.caller.user, now(request)
    token = new_secret()
    with database(request).begin() as session:
        row = m.Invitation(workspace_id=ws_id, email=normal_email(body.email), role=body.role,
                           token_hash=digest(token), invited_by=actor.id,
                           expires_at=at + INVITE_TTL)  # fmt: skip
        session.add(row)
        session.flush()
        audit.record(session, "member.invited", actor.id, workspace_id=ws_id,
                     target_type="invitation", target_id=str(row.id))  # fmt: skip
    page = f"{request.app.state.settings.app_url}/invite?token={token}"
    request.app.state.mailer.send(compose(row.email, "invite", actor.locale, page))
    return _invitation(row, at)


@scoped.get("/invitations")
def list_invitations(ws_id: UUID, request: Request) -> list[Invitation]:
    """The workspace invitations (members.manage)."""
    with database(request)() as session:
        rows = session.scalars(select(m.Invitation).where(m.Invitation.workspace_id == ws_id)
                               .order_by(m.Invitation.created_at)).all()  # fmt: skip
    return [_invitation(row, now(request)) for row in rows]


@scoped.delete("/invitations/{invitation_id}", status_code=204)
def revoke_invitation(ws_id: UUID, invitation_id: UUID, request: Request) -> None:
    """Revoke a pending invitation (members.manage)."""
    with database(request).begin() as session:
        row = session.get(m.Invitation, invitation_id)
        if row is None or row.workspace_id != ws_id:
            raise not_found()
        row.revoked_at = row.revoked_at or now(request)
        audit.record(session, "member.invitation_revoked", request.state.caller.user.id,
                     workspace_id=ws_id, target_type="invitation",
                     target_id=str(invitation_id))  # fmt: skip


@router.post("/invitations/accept")
def accept_invitation(body: TokenRequest, request: Request) -> Workspace:
    """Join the workspace with the emailed token. The signed-in email must match the invitation."""
    user, at = request.state.caller.user, now(request)
    with database(request).begin() as session:
        row = session.scalars(
            select(m.Invitation).where(m.Invitation.token_hash == digest(body.token))
        ).one_or_none()
        if row is None or _status(row, at) != "pending":
            raise ProblemError(400, "TOKEN_INVALID", "Invalid or expired token")
        if row.email != normal_email(user.email):
            raise ProblemError(403, "PERMISSION_DENIED", "This invitation is for someone else")
        row.accepted_at = at
        member = session.scalars(select(m.Membership).where(
            m.Membership.workspace_id == row.workspace_id, m.Membership.user_id == user.id
        )).one_or_none()  # fmt: skip
        if member is None:
            member = m.Membership(workspace_id=row.workspace_id, user_id=user.id, role=row.role)
            session.add(member)
        audit.record(session, "member.joined", user.id, workspace_id=row.workspace_id,
                     target_type="member", target_id=str(user.id))  # fmt: skip
        space = session.get(m.Workspace, row.workspace_id)
    return Workspace(id=space.id, name=space.name, role=member.role, created_at=space.created_at)


@scoped.get("/audit")
def list_audit(ws_id: UUID, cursor: Cursor = None, limit: Limit = 25) -> AuditEventPage:
    """The workspace audit log, newest first (audit.read)."""
    raise not_implemented()


router.include_router(scoped)


def memberships(session, user_id: UUID):
    """`(workspace, role)` pairs of one user, oldest first."""
    return session.execute(
        select(m.Workspace, m.Membership.role)
        .join(m.Membership, m.Membership.workspace_id == m.Workspace.id)
        .where(m.Membership.user_id == user_id)
        .order_by(m.Workspace.created_at)
    ).all()


def _status(row: m.Invitation, at: datetime) -> str:
    if row.accepted_at is not None:
        return "accepted"
    if row.revoked_at is not None:
        return "revoked"
    return "expired" if row.expires_at <= at else "pending"


def _invitation(row: m.Invitation, at: datetime) -> Invitation:
    return Invitation(id=row.id, email=row.email, role=row.role, invited_by=row.invited_by,
                      expires_at=row.expires_at, status=_status(row, at))  # fmt: skip
