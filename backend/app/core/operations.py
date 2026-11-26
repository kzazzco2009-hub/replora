"""Operation contracts: what an operation takes, gives and is configured by (P1.1)."""

from typing import Any

from pydantic import Field

from app.core.artifact_type import ArtifactType
from app.core.model import ContractModel


class Port(ContractModel):
    name: str
    artifact_type: ArtifactType
    required: bool


class OperationContract(ContractModel):
    """A known operation. The frontend renders its parameter form from `params_schema`."""

    id: str
    version: int
    title_key: str = Field(description="i18n key for the operation's name")
    inputs: list[Port]
    outputs: list[Port]
    params_schema: dict[str, Any] = Field(
        description=(
            "JSON Schema, limited to the subset in docs/api_contract.md §5: string, integer, "
            "boolean, enum and array of strings; no oneOf, anyOf or $ref"
        )
    )


class OperationRef(ContractModel):
    id: str
    version: int
