"""Request and response bodies for the §7 runs lifecycle (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import Field, JsonValue

from app.api.models import ApiModel, Page
from app.api.v1.draft_models import Issue, WorkflowDefinition
from app.core.run_state import RunState

__all__ = [
    "ApproveRequest",
    "ResolveRequest",
    "ReviewChoice",
    "Run",
    "RunCounts",
    "RunEvent",
    "RunEvents",
    "RunFromDraft",
    "RunFromWorkflow",
    "RunNode",
    "RunState",
    "RunSummary",
    "RunSummaryPage",
]


PlanHash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$", description="Lowercase hex SHA-256")]


class RunFromDraft(ApiModel):
    draft_id: UUID


class RunFromWorkflow(ApiModel):
    """Replay a saved workflow version on new files (Phase 13)."""

    workflow_id: UUID
    version: Annotated[int, Field(ge=1)]
    file_ids: Annotated[list[UUID], Field(min_length=1, max_length=10)]


class ApproveRequest(ApiModel):
    plan_hash: PlanHash


class ReviewChoice(ApiModel):
    """The user's answer to one of the run's `review_issues`, picked from its `params.options`."""

    code: str
    path: str
    value: JsonValue


class ResolveRequest(ApiModel):
    """Answer a `NEEDS_REVIEW` run. `plan_hash` is the plan the user reviewed."""

    plan_hash: PlanHash
    choices: Annotated[list[ReviewChoice], Field(min_length=1, max_length=100)]


class RunCounts(ApiModel):
    """Reconciliation row counts."""

    matched: int
    value_diff: int
    missing_left: int
    missing_right: int


class RunNode(ApiModel):
    node_id: str
    operation_id: str
    state: str = Field(description="Node state; its values are locked with P1.5 at G1")
    attempt: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_code: str | None = None
    warnings: list[Issue] = []


class Run(ApiModel):
    id: UUID
    state: RunState
    plan_hash: PlanHash
    definition: WorkflowDefinition
    nodes: list[RunNode]
    summary: RunCounts | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    finished_at: datetime | None = None
    review_issues: list[Issue] = Field(
        default=[], description="What the user must decide while the run is `NEEDS_REVIEW`"
    )


class RunSummary(ApiModel):
    """One row of the runs list."""

    id: UUID
    state: RunState
    title: str
    created_at: datetime
    finished_at: datetime | None = None
    summary: RunCounts | None = None


class RunSummaryPage(Page[RunSummary]):
    pass


class RunEvent(ApiModel):
    seq: int
    type: Literal["state_changed", "node_started", "node_finished", "warning"]
    node_id: str | None = None
    payload: dict[str, Any]
    created_at: datetime


class RunEvents(ApiModel):
    """Poll with `after=last_seq` while the state is `QUEUED`, `RUNNING` or `CANCEL_REQUESTED`."""

    events: list[RunEvent]
    last_seq: int
