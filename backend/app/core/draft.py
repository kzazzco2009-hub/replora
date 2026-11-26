"""Planner output: a workflow definition with its explanation and warnings (P1.3)."""

from typing import Any, Self

from pydantic import Field, model_validator

from app.core.model import ContractModel
from app.core.validation import Issue
from app.core.workflow import WorkflowDefinition


class Explanation(ContractModel):
    """TemplatePlanner: `key` + `params` (translated by the client). AI planner: `text`."""

    key: str | None = None
    params: dict[str, Any] | None = None
    text: str | None = Field(default=None, description="Already in `user.locale`")

    @model_validator(mode="after")
    def _key_or_text(self) -> Self:
        if (self.key is None) == (self.text is None):
            raise ValueError("an explanation has either a key or a text")
        if self.params is not None and self.key is None:
            raise ValueError("explanation params go with a key")
        return self


class WorkflowDraft(ContractModel):
    """What a planner returns. It is never trusted: the validator re-checks it (P12.3)."""

    definition: WorkflowDefinition
    explanation: Explanation
    warnings: list[Issue] = []
