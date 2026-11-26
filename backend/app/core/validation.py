"""Validation reports: coded errors and warnings, each at a path in the definition (P1.3)."""

from typing import Any, Self

from pydantic import model_validator

from app.core.model import ContractModel


class Issue(ContractModel):
    code: str
    path: str
    node_id: str | None = None
    params: dict[str, Any] = {}


class ValidationReport(ContractModel):
    valid: bool
    errors: list[Issue]
    warnings: list[Issue]

    @model_validator(mode="after")
    def _valid_means_no_errors(self) -> Self:
        if self.valid == bool(self.errors):
            raise ValueError("valid must be true exactly when there are no errors")
        return self
