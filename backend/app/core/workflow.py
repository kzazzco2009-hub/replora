"""Workflow definitions: typed nodes joined by edges, with IO contracts and policies (P1.2).

The model checks shapes only. Graph rules (unique IDs, known ports, no cycles, limits) belong to
the validator (P2), which always returns a report and never raises.
"""

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import Field, JsonValue, model_validator

from app.core.artifact_type import ArtifactType
from app.core.model import ContractModel
from app.core.operations import OperationRef

Name = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")]
"""A node ID, port name or IO contract name."""

Label = Annotated[str, Field(max_length=100)]
"""A display name in any script, for example Arabic."""


class PortRef(ContractModel):
    """One port of one node."""

    node_id: Name
    port: Name


class Node(ContractModel):
    """One step: a pinned operation version and its parameters."""

    id: Name
    operation: OperationRef
    params: dict[str, JsonValue] = {}
    label: Label | None = None


class Edge(ContractModel):
    """Data flows from an output port to an input port."""

    source: PortRef
    target: PortRef


class InputContract(ContractModel):
    """A file the workflow needs, its expected columns (for replay drift) and the ports it feeds."""

    name: Name
    label: Label | None = None
    artifact_type: ArtifactType
    columns: list[str] = []
    targets: list[PortRef]


class OutputContract(ContractModel):
    """A result the workflow gives, taken from one node's output port."""

    name: Name
    label: Label | None = None
    artifact_type: ArtifactType
    source: PortRef


class ResourcePolicy(ContractModel):
    """Per-run limits. The defaults are the platform maximums (D8, P19.3)."""

    max_files: Annotated[int, Field(ge=1, le=10)] = 10
    max_file_size: Annotated[int, Field(ge=1, le=50 * 1024 * 1024)] = 50 * 1024 * 1024
    node_timeout_seconds: Annotated[int, Field(ge=1, le=120)] = 120
    run_timeout_seconds: Annotated[int, Field(ge=1, le=900)] = 900


class ReviewPolicy(ContractModel):
    """What a run does when a node reports warnings: carry on, or stop as NEEDS_REVIEW."""

    on_warning: Literal["continue", "review"] = "review"


class WorkflowDefinition(ContractModel):
    """The typed workflow that is approved, hashed (P1.4) and run.

    A draft has no `workflow_id` or `workflow_version`. A saved version has both.
    """

    workflow_id: UUID | None = None
    workflow_version: Annotated[int, Field(ge=1)] | None = None
    schema_version: Literal[1] = 1
    nodes: list[Node]
    edges: list[Edge]
    inputs: list[InputContract]
    outputs: list[OutputContract]
    resource_policy: ResourcePolicy = ResourcePolicy()
    review_policy: ReviewPolicy = ReviewPolicy()

    @model_validator(mode="after")
    def _draft_or_saved(self) -> Self:
        if (self.workflow_id is None) != (self.workflow_version is None):
            raise ValueError("workflow_id and workflow_version go together")
        return self
