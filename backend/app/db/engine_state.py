"""Engine state in the database (P4.6): runs, run_nodes and artifacts are saved after each node.

On serverless a worker may die between nodes. The next one loads the run, gets the same ledger
from `run_nodes`, and skips every node already done for the same inputs (T4.4).
"""

import hashlib
import json
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.core.artifact_type import ArtifactType
from app.core.artifacts import ArtifactLineage, ArtifactRef
from app.core.draft import WorkflowDraft
from app.core.engine.executor import Done, NodeKey
from app.core.engine.run import Approval, Run
from app.core.engine.store import Data, new_ref
from app.core.run_state import TERMINAL_STATES, RunState
from app.core.validation import Issue
from app.core.workflow import WorkflowDefinition
from app.db import models as m
from app.db.base import utc_now
from app.db.repos import get, scoped


class DbLedger:
    """The nodes of one run already done, kept in `run_nodes` and committed one by one."""

    def __init__(self, sessions: sessionmaker[Session], workspace_id: UUID, run_id: UUID) -> None:
        self.sessions, self.workspace_id, self.run_id = sessions, workspace_id, run_id

    @staticmethod
    def _hash(key: NodeKey) -> str:
        run_id, node_id, inputs = key
        canonical = json.dumps([str(run_id), node_id, [list(pair) for pair in inputs]])
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _node(self, session: Session, node_id: str) -> m.RunNode | None:
        query = scoped(m.RunNode, self.workspace_id)
        return session.scalars(query.where(m.RunNode.run_id == self.run_id,
                                           m.RunNode.node_id == node_id)).one_or_none()  # fmt: skip

    def _done(self, key: NodeKey) -> m.RunNode | None:
        with self.sessions() as session:
            row = self._node(session, key[1])
        done = row is not None and row.state == "DONE" and row.idempotency_key == self._hash(key)
        return row if done else None

    def __contains__(self, key: object) -> bool:
        return self._done(key) is not None  # type: ignore[arg-type]

    def __getitem__(self, key: NodeKey) -> Done:
        row = self._done(key)
        if row is None:
            raise KeyError(key)
        outputs = {port: ArtifactRef.model_validate(ref) for port, ref in row.outputs.items()}
        return Done(outputs, [Issue.model_validate(w) for w in row.warnings])

    def __setitem__(self, key: NodeKey, done: Done) -> None:
        with self.sessions.begin() as session:
            row = self._node(session, key[1])
            if row is None:
                row = m.RunNode(run_id=self.run_id, node_id=key[1], attempt=0)
                session.add(row)
            row.state, row.idempotency_key, row.finished_at = "DONE", self._hash(key), utc_now()
            row.attempt += 1
            row.outputs = {port: ref.model_dump(mode="json") for port, ref in done.outputs.items()}
            row.warnings = [warning.model_dump(mode="json") for warning in done.warnings]


class DbArtifactStore:
    """Artifact rows in the database; their bytes in the workspace's storage (P6.1).

    With `run_id`, every row it adds belongs to that run, inputs too (their lineage is empty).
    """

    def __init__(self, sessions: sessionmaker[Session], workspace_id: UUID, storage,
                 run_id: UUID | None = None) -> None:  # fmt: skip
        self.sessions, self.workspace_id, self.storage = sessions, workspace_id, storage
        self.run_id = run_id

    def _key(self, ref: ArtifactRef) -> str:
        return f"{self.workspace_id}/{ref.id}"

    def put(self, data: Data, artifact_type: ArtifactType, lineage: ArtifactLineage) -> ArtifactRef:
        ref = new_ref(data, artifact_type, lineage, self.workspace_id)
        self.storage.put(self._key(ref), data.content)
        with self.sessions.begin() as session:
            session.add(m.Artifact(
                id=ref.id, workspace_id=self.workspace_id, run_id=lineage.run_id or self.run_id,
                node_id=lineage.node_id, type=ref.type, format=ref.format, sha256=ref.sha256,
                storage_key=self._key(ref), lineage=lineage.model_dump(mode="json"),
                source=data.source, size=len(data.content),
            ))  # fmt: skip
        return ref

    def read(self, ref: ArtifactRef) -> Data:
        with self.sessions() as session:
            row = get(session, m.Artifact, self.workspace_id, ref.id)
        return Data(self.storage.open(row.storage_key), row.format, row.source)


def save_run(
    sessions: sessionmaker[Session],
    workspace_id: UUID,
    run: Run,
    workflow_version_id: UUID | None = None,
    draft_id: UUID | None = None,
) -> None:
    """Insert the run, or update its state and approval. The plan_hash is fixed at creation."""
    with sessions.begin() as session:
        row = get(session, m.Run, workspace_id, run.id)
        if row is None:
            row = m.Run(id=run.id, workspace_id=workspace_id, plan_hash=run.plan_hash,
                        workflow_version_id=workflow_version_id, draft_id=draft_id,
                        created_at=run.created_at)  # fmt: skip
            session.add(row)
        apply(row, run)


def apply(row: m.Run, run: Run) -> None:
    """Copy the engine run's state and approval onto its row."""
    row.state, row.state_since = run.state.value, run.state_since
    if run.approval is not None:
        row.approved_by, row.approved_at = run.approval.by, run.approval.at
    if run.state in TERMINAL_STATES:
        row.finished_at = run.state_since


def load_run(session: Session, workspace_id: UUID, run_id: UUID) -> Run:
    """The engine's run from its row and its pinned definition. `LookupError` if not found."""
    row = get(session, m.Run, workspace_id, run_id)
    if row is None:
        raise LookupError(run_id)
    approval = None
    if row.approved_at is not None:
        approval = Approval(plan_hash=row.plan_hash, by=row.approved_by, at=row.approved_at)
    return Run(id=row.id, definition=_definition(session, workspace_id, row),
               state=RunState(row.state), created_at=row.created_at,
               state_since=row.state_since or row.created_at, approval=approval)  # fmt: skip


def _definition(session: Session, workspace_id: UUID, row: m.Run) -> WorkflowDefinition:
    if row.definition is not None:
        return WorkflowDefinition.model_validate(row.definition)
    if row.workflow_version_id is not None:
        version = get(session, m.WorkflowVersion, workspace_id, row.workflow_version_id)
        return WorkflowDefinition.model_validate(version.definition)
    draft = get(session, m.Draft, workspace_id, row.draft_id)
    return WorkflowDraft.model_validate(draft.draft).definition
