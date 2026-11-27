"""Workspace-scoped queries (P4.5, S-14).

`scoped` is the only place a query on a tenant table is built, and it always filters by the
workspace. A child table is joined to the parent that holds its workspace. A lint test
(`tests/unit/test_tenant_scoping_lint.py`) fails if `app/` queries a tenant table any other way.
Another workspace's row is simply not found, so the API answers 404 (S-22).
"""

from uuid import UUID

from sqlalchemy import Select, select, tuple_
from sqlalchemy.orm import Session

from app.db.models import Artifact, Draft, File, Run, RunEvent, RunNode, Workflow, WorkflowVersion

TENANT = (File, Workflow, Draft, Run, Artifact)
"""Tables with their own `workspace_id`."""

CHILD = {WorkflowVersion: (Workflow, "workflow_id"), RunNode: (Run, "run_id"),
         RunEvent: (Run, "run_id")}  # fmt: skip
"""Tables that belong to a workspace through their parent."""


def scoped[M](model: type[M], workspace_id: UUID) -> Select[tuple[M]]:
    """`SELECT model` limited to one workspace."""
    if model in CHILD:
        parent, column = CHILD[model]
        return (
            select(model)
            .join(parent, getattr(model, column) == parent.id)
            .where(parent.workspace_id == workspace_id)
        )
    return select(model).where(model.workspace_id == workspace_id)


def get[M](session: Session, model: type[M], workspace_id: UUID, row_id: UUID) -> M | None:
    """One row by ID, or None when it doesn't exist **or** belongs to another workspace."""
    return session.scalars(scoped(model, workspace_id).where(model.id == row_id)).one_or_none()


def page[M](
    session: Session, model: type[M], workspace_id: UUID, limit: int, after: M | None = None
) -> list[M]:
    """Newest first, `limit` rows, continuing after the last row of the previous page."""
    return page_query(session, scoped(model, workspace_id), model, limit, after)


def page_query[M](
    session: Session, query: Select[tuple[M]], model: type[M], limit: int, after: M | None = None
) -> list[M]:
    """`page` for a query already scoped by `scoped` (and maybe filtered further)."""
    if after is not None:
        query = query.where(tuple_(model.created_at, model.id) < (after.created_at, after.id))
    query = query.order_by(model.created_at.desc(), model.id.desc()).limit(limit)
    return list(session.scalars(query))
