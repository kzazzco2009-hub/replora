"""Privacy rights (P5.10, S-29): export of a user's own data, and deletion after a grace period.

The export holds the profile, the user's memberships, and the content of their personal workspace
(workflows with their versions, drafts, runs, file records). It never holds password hashes, MFA
secrets, or anything from a workspace shared with others.

Deletion signs the user out at once and blocks sign-in. After the grace period, the purge removes
the user and their personal workspace; their audit entries stay, with no actor.
"""

import io
import json
import zipfile
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.problem import ProblemError
from app.auth.one_time import revoke_all_sessions
from app.db import models as m
from app.db.repos import scoped


def export_key(user_id: UUID | str, export_id: UUID | str) -> str:
    """Where an export lives in storage; only its owner's id can reach it."""
    return f"exports/{user_id}/{export_id}"


def _rows(rows, *fields: str) -> list[dict[str, Any]]:
    return [{field: getattr(row, field) for field in fields} for row in rows]


def export_archive(session: Session, user: m.User) -> bytes:
    personal = session.scalars(select(m.Workspace).where(
        m.Workspace.owner_id == user.id, m.Workspace.personal.is_(True))).one()  # fmt: skip
    ws = personal.id
    flows = session.scalars(scoped(m.Workflow, ws)).all()
    content = {
        "profile.json": _rows([user], "id", "email", "display_name", "locale", "theme",
                              "timezone", "email_verified_at", "created_at")[0],
        "workspaces.json": [
            {"id": w.id, "name": w.name, "role": role} for w, role in session.execute(
                select(m.Workspace, m.Membership.role)
                .join(m.Membership, m.Membership.workspace_id == m.Workspace.id)
                .where(m.Membership.user_id == user.id))
        ],
        "workflows.json": _rows(flows, "id", "name", "latest_version", "created_at"),
        "workflow_versions.json": _rows(session.scalars(scoped(m.WorkflowVersion, ws)).all(),
                                        "workflow_id", "version", "definition", "plan_hash"),
        "drafts.json": _rows(session.scalars(scoped(m.Draft, ws)).all(),
                             "id", "prompt", "draft", "planner", "created_at"),
        "runs.json": _rows(session.scalars(scoped(m.Run, ws)).all(),
                           "id", "state", "plan_hash", "created_at", "finished_at"),
        "files.json": _rows(session.scalars(scoped(m.File, ws)).all(),
                            "id", "display_name", "detected_type", "size", "sha256", "created_at"),
    }  # fmt: skip
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in content.items():
            archive.writestr(name, json.dumps(value, default=str, ensure_ascii=False, indent=2))
    return buffer.getvalue()


def request_deletion(session: Session, user: m.User, now: datetime) -> None:
    """Mark the account deleted and end its sessions; refused while it owns a shared workspace."""
    shared = session.scalars(select(m.Workspace.id).where(
        m.Workspace.owner_id == user.id, m.Workspace.personal.is_(False))).first()  # fmt: skip
    if shared is not None:
        raise ProblemError(409, "OWNS_SHARED_WORKSPACE", "Hand over or delete shared workspaces")
    user.deleted_at = now
    revoke_all_sessions(session, user, now)


def purge_deleted(session: Session, storage, now: datetime, grace: timedelta) -> int:
    """Remove the users whose grace period is over, with their personal workspace and its files'
    bytes in storage (S-29). The count."""
    users = session.scalars(select(m.User).where(m.User.deleted_at <= now - grace)).all()
    for user in users:
        for space in session.scalars(select(m.Workspace).where(m.Workspace.owner_id == user.id)):
            for file in session.scalars(scoped(m.File, space.id)):
                storage.delete(file.storage_key)
            session.delete(space)
        session.flush()
        session.delete(user)
    return len(users)
