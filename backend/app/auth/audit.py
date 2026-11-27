"""The audit log (P5.7, S-26). Every auth event is recorded; emails and IPs never in clear.

When a user is deleted, their entries stay with the actor set to NULL (S-29).
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.db import models as m


def record(
    session: Session,
    action: str,
    actor_id: UUID | None,
    *,
    workspace_id: UUID | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    ip_hash: str | None = None,
) -> None:
    session.add(m.AuditEvent(action=action, actor_id=actor_id, workspace_id=workspace_id,
                             target_type=target_type, target_id=target_id,
                             ip_hash=ip_hash))  # fmt: skip
