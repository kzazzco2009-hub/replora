"""P4.5 workspace-scoped repositories: T4.3 (no cross-workspace rows) and S-15 payloads."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect

from app.db import models as m
from app.db.base import Base
from app.db.engine import make_engine, make_sessions
from app.db.repos import CHILD, TENANT, get, page, scoped

T0 = datetime(2026, 11, 26, 12, tzinfo=UTC)


def seed(session, name: str, minutes: int = 0):
    """One row of every tenant and child table in a new workspace."""
    owner = m.User(email=f"{name}@example.com", password_hash="x")
    session.add(owner)
    session.flush()
    ws = m.Workspace(name=name, owner_id=owner.id)
    session.add(ws)
    session.flush()
    at = T0 + timedelta(minutes=minutes)
    flow = m.Workflow(workspace_id=ws.id, name=name, created_at=at)
    draft = m.Draft(workspace_id=ws.id, draft={}, plan_hash="a" * 64, planner="template")
    file = m.File(workspace_id=ws.id, storage_key=name, display_name=name, size=1,
                  status="ready")  # fmt: skip
    session.add_all([flow, draft, file])
    session.flush()
    version = m.WorkflowVersion(workflow_id=flow.id, version=1, definition={}, plan_hash="a" * 64)
    run = m.Run(workspace_id=ws.id, state="QUEUED", plan_hash="a" * 64)
    session.add_all([version, run])
    session.flush()
    session.add_all([
        m.RunNode(run_id=run.id, node_id="a", state="DONE"),
        m.RunEvent(run_id=run.id, seq=1, type="x", payload={}),
        m.Artifact(workspace_id=ws.id, run_id=run.id, type="TabularArtifact", format="csv",
                   sha256="b" * 64, storage_key=name, lineage={}),
    ])  # fmt: skip
    return ws


@pytest.fixture
def db(db_url):
    engine = make_engine(db_url)
    Base.metadata.create_all(engine)
    sessions = make_sessions(engine)
    with sessions.begin() as session:
        a, b = seed(session, "a"), seed(session, "b")
    return sessions, a.id, b.id


def test_every_table_with_a_workspace_is_scoped():
    with_workspace = {mapper.class_ for mapper in Base.registry.mappers
                      if "workspace_id" in inspect(mapper.class_).columns}  # fmt: skip
    assert with_workspace - {m.Membership, m.Invitation, m.AuditEvent} == set(TENANT)
    assert set(CHILD) == {m.WorkflowVersion, m.RunNode, m.RunEvent}


@pytest.mark.parametrize("model", [*TENANT, *CHILD], ids=lambda model: model.__tablename__)
def test_a_workspace_never_sees_another_workspaces_rows(db, model):
    sessions, a, b = db
    with sessions() as session:
        mine = session.scalars(scoped(model, a)).all()
        theirs = session.scalars(scoped(model, b)).all()
    assert len(mine) == len(theirs) == 1
    assert {row.id for row in mine}.isdisjoint({row.id for row in theirs})


@pytest.mark.parametrize("model", [*TENANT, *CHILD], ids=lambda model: model.__tablename__)
def test_get_by_id_from_another_workspace_is_none(db, model):
    sessions, a, b = db
    with sessions() as session:
        theirs = session.scalars(scoped(model, b)).one()
        assert get(session, model, b, theirs.id) is theirs
        assert get(session, model, a, theirs.id) is None


def test_pages_are_newest_first_and_continue_after_a_cursor(db):
    sessions, a, _ = db
    with sessions.begin() as session:
        for minutes in (1, 2, 3):
            session.add(m.Workflow(workspace_id=a, name=f"w{minutes}",
                                   created_at=T0 + timedelta(minutes=minutes)))  # fmt: skip
    with sessions() as session:
        first = page(session, m.Workflow, a, limit=2)
        rest = page(session, m.Workflow, a, limit=2, after=first[-1])
    assert [w.name for w in first] == ["w3", "w2"]
    assert [w.name for w in rest] == ["w1", "a"]


@pytest.mark.parametrize("payload", ["' OR 1=1--", "x'; DROP TABLE workflows; --", "%' OR '%"])
def test_sql_payloads_are_data_not_sql(db, payload):
    sessions, a, _ = db
    with sessions.begin() as session:
        session.add(m.Workflow(workspace_id=a, name=payload))
    with sessions() as session:
        found = session.scalars(scoped(m.Workflow, a).where(m.Workflow.name == payload)).all()
        assert [w.name for w in found] == [payload]
        assert len(session.scalars(scoped(m.Workflow, a)).all()) == 2
