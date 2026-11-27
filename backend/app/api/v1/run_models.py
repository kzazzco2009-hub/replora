"""Request and response bodies for the §7 runs lifecycle (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, JsonValue, TypeAdapter

from app.api.models import ApiModel, Page
from app.api.v1.draft_models import Issue, WorkflowDefinition
from app.core.run_state import RunState

__all__ = [
    "EVENT",
    "ApproveRequest",
    "NodeFinishedEvent",
    "NodeFinishedPayload",
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
    "StateChangedEvent",
    "StateChangedPayload",
    "WarningEvent",
    "WarningPayload",
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
    approval_expires_at: datetime | None = Field(
        default=None,
        description="When an `AWAITING_APPROVAL` run expires (`APPROVAL_TTL_HOURS`); else null",
    )
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


class StateChangedPayload(ApiModel):
    state: RunState


class NodeFinishedPayload(ApiModel):
    warnings: list[Issue]


class WarningPayload(ApiModel):
    issue: Issue


class _Event(ApiModel):
    seq: int = Field(description="1, 2, … within the run; strictly increasing")
    created_at: datetime


class StateChangedEvent(_Event):
    type: Literal["state_changed"]
    node_id: None = None
    payload: StateChangedPayload


class NodeFinishedEvent(_Event):
    type: Literal["node_finished"]
    node_id: str
    payload: NodeFinishedPayload


class WarningEvent(_Event):
    type: Literal["warning"]
    node_id: str | None = None
    payload: WarningPayload


type RunEvent = Annotated[
    StateChangedEvent | NodeFinishedEvent | WarningEvent, Field(discriminator="type")
]
EVENT = TypeAdapter(RunEvent)


class RunEvents(ApiModel):
    """Poll with `after=last_seq` while the state is `QUEUED`, `RUNNING` or `CANCEL_REQUESTED`."""

    events: list[RunEvent]
    last_seq: int
