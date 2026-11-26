"""§8 workflows and replay (docs/api_contract.md). 501 stubs until Phase 13."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query

from app.api.models import Cursor, Limit
from app.api.problem import ERROR_RESPONSES, NOT_FOUND_RESPONSE, not_implemented
from app.api.v1.workflow_models import (
    ReplayCheck,
    ReplayCheckRequest,
    Workflow,
    WorkflowCreate,
    WorkflowDetail,
    WorkflowPage,
    WorkflowVersion,
    WorkflowVersionCreate,
)

router = APIRouter(
    prefix="/workspaces/{ws_id}/workflows",
    tags=["workflows"],
    responses=ERROR_RESPONSES | NOT_FOUND_RESPONSE,
)


@router.post("", status_code=201, name="create")
def create_workflow(ws_id: UUID, body: WorkflowCreate) -> Workflow:
    """Save a draft as a workflow (version 1)."""
    raise not_implemented()


@router.get("", name="list")
def list_workflows(
    ws_id: UUID,
    cursor: Cursor = None,
    limit: Limit = 25,
    q: Annotated[str | None, Query(max_length=100, description="Search by name")] = None,
) -> WorkflowPage:
    """The workspace workflows, newest first."""
    raise not_implemented()


@router.get("/{workflow_id}", name="get")
def get_workflow(ws_id: UUID, workflow_id: UUID) -> WorkflowDetail:
    """One workflow with its version history."""
    raise not_implemented()


@router.get("/{workflow_id}/versions/{version}", name="get_version")
def get_workflow_version(
    ws_id: UUID, workflow_id: UUID, version: Annotated[int, Path(ge=1)]
) -> WorkflowVersion:
    """One immutable version, with its definition."""
    raise not_implemented()


@router.post("/{workflow_id}/replay-check", name="replay_check")
def check_replay(ws_id: UUID, workflow_id: UUID, body: ReplayCheckRequest) -> ReplayCheck:
    """Compare new files with the latest version's input columns, before a replay run."""
    raise not_implemented()


@router.post("/{workflow_id}/versions", status_code=201, name="create_version")
def create_workflow_version(
    ws_id: UUID, workflow_id: UUID, body: WorkflowVersionCreate
) -> WorkflowVersion:
    """A new version from a column mapping. 409 `BASE_VERSION_STALE` if not built on the latest."""
    raise not_implemented()


@router.delete("/{workflow_id}", status_code=204, name="delete")
def delete_workflow(ws_id: UUID, workflow_id: UUID) -> None:
    """Soft delete. Past runs keep their pinned version."""
    raise not_implemented()
