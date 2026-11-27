"""The database job worker (P8.2, P8.3): `uv run python -m app.worker`.

A `run_step` job runs **one** node of its run, then enqueues the next step in the same
transaction that finishes the job. No job lasts longer than a node, which is the chain a
serverless function follows (P8.8). The engine already resumes a RUNNING run and skips the nodes
recorded in `run_nodes` (P4.6), so a step is `execute` with a ledger that stops the job right
after it records one new node.

A worker that dies mid-node leaves its job leased. When the lease ends another worker claims it
and runs the node again: nothing was recorded for it. A failed node is not recorded either, so
each later step meets it again (it fails the same way) on the way to the next node.
"""

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.core.artifact_type import ArtifactType
from app.core.artifacts import ArtifactLineage, ArtifactRef
from app.core.engine.executor import Done, Execution, NodeKey, execute
from app.core.engine.run import Run
from app.core.engine.store import Data
from app.core.run_state import RunState
from app.db import models as m
from app.db.engine import make_engine, make_sessions
from app.db.engine_state import DbArtifactStore, DbLedger, apply, load_run
from app.db.jobs import claim, enqueue, finish
from app.db.repos import get, scoped
from app.db.run_events import emit
from app.housekeeping import EVERY, housekeep
from app.observability import configure_logging
from app.ops.registry import HANDLERS, REGISTRY
from app.storage.local import LocalStorage

LEASE = timedelta(minutes=5)
ACTIVE = {RunState.QUEUED, RunState.RUNNING, RunState.CANCEL_REQUESTED}
logger = logging.getLogger(__name__)


class _Stepped(BaseException):
    """This job's node is done: stop here and let the next job continue the run."""


class _OneNode:
    """The run's ledger, which ends the job after recording one new node and its event."""

    def __init__(self, ledger: DbLedger, sessions: sessionmaker[Session], clock) -> None:
        self.ledger, self.sessions, self.clock = ledger, sessions, clock

    def __contains__(self, key: object) -> bool:
        return key in self.ledger

    def __getitem__(self, key: NodeKey) -> Done:
        return self.ledger[key]

    def __setitem__(self, key: NodeKey, done: Done) -> None:
        self.ledger[key] = done
        with self.sessions.begin() as session:
            emit(session, key[0], "node_finished", self.clock(), node_id=key[1],
                 warnings=[w.model_dump(mode="json") for w in done.warnings])  # fmt: skip
        raise _Stepped


def run_step(sessions: sessionmaker[Session], storage, ws_id: UUID, run_id: UUID,
             clock: Callable[[], datetime]) -> bool:  # fmt: skip
    """Advance the run by one node. True when it needs another step."""
    with sessions() as session:
        run = load_run(session, ws_id, run_id)
        file_ids = get(session, m.Run, ws_id, run_id).file_ids
    if run.state not in ACTIVE:
        return False
    store = DbArtifactStore(sessions, ws_id, storage, run_id=run_id)
    try:
        done = execute(run, REGISTRY, HANDLERS, store, _inputs(sessions, store, run, file_ids),
                       ledger=_OneNode(DbLedger(sessions, ws_id, run_id), sessions, clock),
                       clock=clock, cancelled=lambda: _asked_to_cancel(sessions, ws_id, run_id),
                       checkpoint=lambda r: _save(sessions, ws_id, r))  # fmt: skip
    except _Stepped:
        return True
    _record_issues(sessions, ws_id, done)
    return False


def _inputs(sessions, store: DbArtifactStore, run: Run, file_ids: list[str]) -> dict:
    """The run's input artifacts by input name, made from its files on the first step only."""
    ws_id = store.workspace_id
    with sessions() as session:
        made = session.scalars(scoped(m.Artifact, ws_id).where(
            m.Artifact.run_id == run.id, m.Artifact.node_id.is_(None))).all()  # fmt: skip
        known = {row.source["file_id"]: _ref(row) for row in made}
        files = {str(f.id): f for f in session.scalars(
            scoped(m.File, ws_id).where(m.File.id.in_([UUID(i) for i in file_ids])))}  # fmt: skip
    for file_id in file_ids:
        if file_id not in known:
            file = files[file_id]
            data = Data(store.storage.open(file.storage_key), file.detected_type,
                        {"file": file.display_name, "file_id": file_id})  # fmt: skip
            known[file_id] = store.put(data, ArtifactType.RAW_FILE, ArtifactLineage())
    return {i.name: known[f] for i, f in zip(run.definition.inputs, file_ids, strict=True)}


def _ref(row: m.Artifact) -> ArtifactRef:
    return ArtifactRef(id=row.id, type=row.type, format=row.format, sha256=row.sha256,
                       workspace_id=row.workspace_id,
                       lineage=ArtifactLineage.model_validate(row.lineage))  # fmt: skip


def _asked_to_cancel(sessions, ws_id: UUID, run_id: UUID) -> bool:
    with sessions() as session:
        return get(session, m.Run, ws_id, run_id).state == RunState.CANCEL_REQUESTED


def _save(sessions, ws_id: UUID, run: Run) -> None:
    """The engine's checkpoint: the run's new state, and its event when it changed."""
    with sessions.begin() as session:
        row = get(session, m.Run, ws_id, run.id)
        changed = row.state != run.state.value
        apply(row, run)
        if changed:
            emit(session, run.id, "state_changed", run.state_since, state=row.state)


def _record_issues(sessions, ws_id: UUID, done: Execution) -> None:
    with sessions.begin() as session:
        row = get(session, m.Run, ws_id, done.run.id)
        row.issues = [issue.model_dump(mode="json") for issue in done.issues]


def work_once(sessions: sessionmaker[Session], storage, clock=lambda: datetime.now(UTC)) -> bool:
    """Claim one due job and do it. False when there was none."""
    job = claim(sessions, clock(), LEASE)
    if job is None:
        return False
    more = run_step(sessions, storage, UUID(job.payload["workspace_id"]),
                    UUID(job.payload["run_id"]), clock)  # fmt: skip
    with sessions.begin() as session:
        finish(session, job.id)
        if more:
            enqueue(session, job.kind, job.payload, clock())
    return True


def main() -> None:
    configure_logging()
    settings = Settings()
    sessions = make_sessions(make_engine(settings.database_url))
    storage = LocalStorage(settings.data_dir / "storage", "worker: never signs")
    due = datetime.now(UTC)
    while True:
        at = datetime.now(UTC)
        if at >= due:
            logger.info("housekeeping %s", housekeep(sessions, storage, settings, at))
            due = at + EVERY
        if not work_once(sessions, storage):
            time.sleep(1)


if __name__ == "__main__":
    main()
