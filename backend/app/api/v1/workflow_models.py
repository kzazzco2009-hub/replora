"""Request and response bodies for §8 workflows and replay (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.api.models import ApiModel, Page
from app.api.v1.draft_models import WorkflowDefinition
from app.api.v1.run_models import PlanHash

FileIds = Annotated[list[UUID], Field(min_length=1, max_length=10)]


class WorkflowCreate(ApiModel):
    """Save a draft as version 1 of a new workflow."""

    name: Annotated[str, Field(min_length=1, max_length=100)]
    draft_id: UUID


class Workflow(ApiModel):
    id: UUID
    name: str
    latest_version: int
    created_by: UUID
    created_at: datetime


class WorkflowPage(Page[Workflow]):
    pass


class WorkflowVersionInfo(ApiModel):
    version: int
    plan_hash: PlanHash
    created_at: datetime


class WorkflowDetail(Workflow):
    versions: list[WorkflowVersionInfo]


class WorkflowVersion(ApiModel):
    """Immutable once created (P13.1)."""

    workflow_id: UUID
    version: int
    definition: WorkflowDefinition
    plan_hash: PlanHash
    created_at: datetime


class ReplayCheckRequest(ApiModel):
    file_ids: FileIds


class ColumnSuggestion(ApiModel):
    """A likely match for a missing column, offered in the mapping editor."""

    expected: str
    found: str


class InputDrift(ApiModel):
    input: str = Field(description="The workflow input whose columns differ")
    expected_columns: list[str]
    found_columns: list[str]
    suggestions: list[ColumnSuggestion]


class ReplayCheck(ApiModel):
    compatible: bool
    drift: list[InputDrift]


class WorkflowVersionCreate(ApiModel):
    """A new version from a column mapping; it needs a new approval (P13.3)."""

    base_version: Annotated[int, Field(ge=1)]
    mapping: dict[str, str] = Field(description="Expected column → column found in the new files")
