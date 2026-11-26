"""Request and response bodies for §6 templates and drafts (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import Field, RootModel

from app.api.models import ApiModel
from app.core.artifact_type import ArtifactType
from app.core.draft import Explanation
from app.core.validation import Issue, ValidationReport

__all__ = [
    "AiDisclosure",
    "Draft",
    "DraftCreate",
    "DraftUpdate",
    "Explanation",
    "Issue",
    "Planner",
    "Template",
    "TemplateInput",
    "ValidationReport",
    "WorkflowDefinition",
]

Planner = Literal["template", "ai"]
"""`mock` exists only in test builds and is never exposed."""


class WorkflowDefinition(RootModel[dict[str, Any]]):
    """The typed workflow. An object until the Phase 1 JSON Schema (`contracts/schemas/`)."""


class TemplateInput(ApiModel):
    """One file a template needs, for example the left file of a reconciliation."""

    title_key: str = Field(description="i18n key for the input's label")
    artifact_type: ArtifactType


class Template(ApiModel):
    id: str
    title_key: str
    description_key: str
    required_inputs: list[TemplateInput]


class DraftCreate(ApiModel):
    file_ids: Annotated[list[UUID], Field(min_length=1, max_length=10)]
    prompt: Annotated[str, Field(max_length=4000)] = ""
    planner: Planner
    template_id: str | None = Field(default=None, description="Required when planner=template")
    share_samples: bool = Field(default=False, description="Consent to send sample rows to AI")


class DraftUpdate(ApiModel):
    """The **full** definition; the server re-validates it and computes the new `plan_hash`."""

    definition: WorkflowDefinition


class AiDisclosure(ApiModel):
    """What was sent to the AI planner. Empty for template drafts."""

    sent_fields: list[str]
    samples_sent: bool


class Draft(ApiModel):
    id: UUID
    prompt: str
    planner: Planner
    definition: WorkflowDefinition
    plan_hash: str = Field(description="SHA-256 of the canonical definition (P1.4)")
    explanation: Explanation
    ai_disclosure: AiDisclosure
    validation: ValidationReport
    created_at: datetime
