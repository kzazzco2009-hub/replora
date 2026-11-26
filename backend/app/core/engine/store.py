"""An in-memory artifact store for the engine (P3.3). Phase 4 puts it behind the database."""

import hashlib
from dataclasses import dataclass
from uuid import UUID, uuid7

from app.core.artifact_type import ArtifactType
from app.core.artifacts import ArtifactLineage, ArtifactRef


@dataclass(frozen=True, slots=True)
class Data:
    """What a handler reads from an input port or writes to an output port."""

    content: bytes
    format: str


class ArtifactStore:
    """Artifacts of one workspace, by ID. Every artifact is hashed and carries its lineage."""

    def __init__(self, workspace_id: UUID) -> None:
        self.workspace_id = workspace_id
        self._content: dict[UUID, Data] = {}

    def put(self, data: Data, artifact_type: ArtifactType, lineage: ArtifactLineage) -> ArtifactRef:
        ref = ArtifactRef(
            id=uuid7(),
            type=artifact_type,
            format=data.format,
            sha256=hashlib.sha256(data.content).hexdigest(),
            workspace_id=self.workspace_id,
            lineage=lineage,
        )
        self._content[ref.id] = data
        return ref

    def read(self, ref: ArtifactRef) -> Data:
        return self._content[ref.id]
