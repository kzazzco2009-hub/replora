"""Artifact stores for the engine (P3.3): in memory here, the database in `app.db.engine_state`."""

import hashlib
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid7

from app.core.artifact_type import ArtifactType
from app.core.artifacts import ArtifactLineage, ArtifactRef


@dataclass(frozen=True, slots=True)
class Data:
    """What a handler reads from an input port or writes to an output port."""

    content: bytes
    format: str


class Store(Protocol):
    """Where the executor keeps artifacts. Every artifact is hashed and carries its lineage."""

    workspace_id: UUID

    def put(
        self, data: Data, artifact_type: ArtifactType, lineage: ArtifactLineage
    ) -> ArtifactRef: ...
    def read(self, ref: ArtifactRef) -> Data: ...


def new_ref(
    data: Data, artifact_type: ArtifactType, lineage: ArtifactLineage, workspace_id: UUID
) -> ArtifactRef:
    return ArtifactRef(
        id=uuid7(),
        type=artifact_type,
        format=data.format,
        sha256=hashlib.sha256(data.content).hexdigest(),
        workspace_id=workspace_id,
        lineage=lineage,
    )


class ArtifactStore:
    """Artifacts of one workspace, in memory."""

    def __init__(self, workspace_id: UUID) -> None:
        self.workspace_id = workspace_id
        self._content: dict[UUID, Data] = {}

    def put(self, data: Data, artifact_type: ArtifactType, lineage: ArtifactLineage) -> ArtifactRef:
        ref = new_ref(data, artifact_type, lineage, self.workspace_id)
        self._content[ref.id] = data
        return ref

    def read(self, ref: ArtifactRef) -> Data:
        return self._content[ref.id]
