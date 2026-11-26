"""Artifact references: a typed, hashed, workspace-owned result with its lineage (P1.1)."""

from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, model_validator

from app.core.artifact_type import ArtifactType
from app.core.model import ContractModel
from app.core.operations import OperationRef

__all__ = ["ArtifactLineage", "ArtifactRef", "ArtifactType"]

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$", description="Lowercase hex SHA-256")]
Format = Annotated[
    str, Field(pattern=r"^[a-z0-9]{1,16}$", description="File format, for example `csv`")
]


class ArtifactLineage(ContractModel):
    """How an artifact came to be.

    An uploaded file has no run, node, operation or parents. A produced artifact names the run,
    node and operation version that made it, and the artifacts it was made from.
    """

    run_id: UUID | None = None
    node_id: str | None = None
    operation: OperationRef | None = None
    parents: list[UUID] = []

    @model_validator(mode="after")
    def _upload_or_produced(self) -> Self:
        produced = (self.run_id, self.node_id, self.operation)
        if any(produced) and not all(produced):
            raise ValueError("lineage needs run_id, node_id and operation together")
        if self.parents and not all(produced):
            raise ValueError("lineage parents need the run, node and operation that used them")
        return self


class ArtifactRef(ContractModel):
    """A reference to a stored artifact. It is owned by exactly one workspace."""

    id: UUID
    type: ArtifactType
    format: Format
    sha256: Sha256
    workspace_id: UUID
    lineage: ArtifactLineage
