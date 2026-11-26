"""P4.6 engine state is saved after each node, so a killed run resumes without redoing (T4.4)."""

import io
import json
import zipfile
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fakes import HANDLERS, PIPELINE, REGISTRY

from app.core.artifact_type import ArtifactType as T
from app.core.artifacts import ArtifactLineage
from app.core.engine.executor import Done, execute
from app.core.engine.run import approve, new_run, transition
from app.core.engine.store import Data
from app.core.run_state import RunAction, RunState
from app.db import models as m
from app.db.base import Base
from app.db.engine import make_engine, make_sessions
from app.db.engine_state import DbArtifactStore, DbLedger, load_run, save_run
from app.db.repos import scoped

NOW = datetime(2026, 11, 26, 12, tzinfo=UTC)


class Killed(BaseException):
    """The process dying: not an operation failure, so nothing catches it."""


def bundle() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("orders.csv", "order_id,amount\nA1,10\n")
        archive.writestr("payments.json", json.dumps([{"order_id": "A1", "amount": 10}]))
    return buffer.getvalue()


@pytest.fixture
def world(tmp_path):
    """A database file, a blob folder, a workspace with a saved pipeline and a queued run."""
    url = f"sqlite:///{(tmp_path / 'c.db').as_posix()}"
    Base.metadata.create_all(make_engine(url))
    sessions = make_sessions(make_engine(url))
    with sessions.begin() as session:
        owner = m.User(email="s@example.com", password_hash="x")
        session.add(owner)
        session.flush()
        ws = m.Workspace(name="s", owner_id=owner.id)
        session.add(ws)
        session.flush()
        flow = m.Workflow(workspace_id=ws.id, name="p")
        session.add(flow)
        session.flush()
        version = m.WorkflowVersion(workflow_id=flow.id, version=1, plan_hash="a" * 64,
                                    definition=PIPELINE.model_dump(mode="json"))  # fmt: skip
        session.add(version)
    run = transition(new_run(PIPELINE, NOW), RunAction.VALIDATE, NOW)
    run = transition(run, RunAction.REQUEST_APPROVAL, NOW)
    run = approve(run, run.plan_hash, owner.id, NOW)
    save_run(sessions, ws.id, run, workflow_version_id=version.id)
    return url, tmp_path / "blobs", ws.id, run.id


def attempt(world, handlers):
    """One worker process: fresh engine and sessions, the run loaded from the database."""
    url, blobs, ws, run_id = world
    sessions = make_sessions(make_engine(url))
    store = DbArtifactStore(sessions, ws, blobs)
    with sessions() as session:
        run = load_run(session, ws, run_id)
    upload = store.put(Data(bundle(), "zip"), T.RAW_FILE, ArtifactLineage())
    return execute(run, REGISTRY, handlers, store, {"bundle": upload},
                   ledger=DbLedger(sessions, ws, run_id), clock=lambda: NOW,
                   checkpoint=lambda r: save_run(sessions, ws, r))  # fmt: skip


def counting(calls, kill_at=None):
    def wrap(key, fn):
        def call(inputs, params):
            if key[0] == kill_at:
                raise Killed
            calls.append(key[0])
            return fn(inputs, params)

        return call

    return {key: wrap(key, fn) for key, fn in HANDLERS.items()}


def test_a_killed_run_resumes_without_re_executing_done_nodes(world):
    calls: list[str] = []
    with pytest.raises(Killed):
        attempt(world, counting(calls, kill_at="fake_parse_json"))
    assert calls == ["fake_unzip", "fake_parse_csv"]
    url, _, ws, run_id = world
    with make_sessions(make_engine(url))() as session:
        assert load_run(session, ws, run_id).state is RunState.RUNNING
        done = session.scalars(scoped(m.RunNode, ws)).all()
        assert sorted(node.node_id for node in done) == ["orders", "unzip"]

    result = attempt(world, counting(calls))
    assert calls == ["fake_unzip", "fake_parse_csv", "fake_parse_json", "fake_compare",
                     "fake_render"]  # fmt: skip
    assert result.run.state is RunState.SUCCEEDED
    with make_sessions(make_engine(url))() as session:
        assert load_run(session, ws, run_id).state is RunState.SUCCEEDED
        assert len(session.scalars(scoped(m.RunNode, ws)).all()) == 5


def test_artifacts_are_rows_with_their_lineage_and_content(world):
    result = attempt(world, counting([]))
    url, blobs, ws, _ = world
    report = result.outputs["report"]
    with make_sessions(make_engine(url))() as session:
        row = session.scalars(scoped(m.Artifact, ws).where(m.Artifact.id == report.id)).one()
        assert (row.run_id, row.node_id, row.sha256) == (result.run.id, "render", report.sha256)
        assert row.lineage == report.lineage.model_dump(mode="json")
    store = DbArtifactStore(make_sessions(make_engine(url)), ws, blobs)
    assert store.read(report).content.startswith(b"key,status,left,right\n")


def test_the_run_row_keeps_state_and_approval(world):
    url, _, ws, run_id = world
    with make_sessions(make_engine(url))() as session:
        run = load_run(session, ws, run_id)
    assert run.state is RunState.QUEUED
    assert run.approval is not None and run.approval.plan_hash == run.plan_hash
    assert run.definition == PIPELINE


def test_a_run_is_not_found_from_another_workspace(world):
    url, _, _, run_id = world
    with make_sessions(make_engine(url))() as session, pytest.raises(LookupError):
        load_run(session, uuid4(), run_id)


def test_a_done_node_with_other_inputs_is_not_in_the_ledger(world):
    url, _, ws, run_id = world
    ledger = DbLedger(make_sessions(make_engine(url)), ws, run_id)
    key = (run_id, "unzip", (("archive", "a" * 64),))
    ledger[key] = Done({}, [])
    assert key in ledger
    assert (run_id, "unzip", (("archive", "b" * 64),)) not in ledger
