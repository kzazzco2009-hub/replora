"""P4.2 and P4.3: the tables, their indexes (T4.6), UUIDv7 and UTC (T4.5), and uniqueness (T4.7)."""

import re
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid7

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, StatementError

from app.config import REPO_ROOT
from app.db import models
from app.db.base import Base
from app.db.engine import make_engine, make_sessions

PLAN = (REPO_ROOT / "docs" / "plan.md").read_text(encoding="utf-8")
SECTION = PLAN[PLAN.index("## 6. Database tables") : PLAN.index("## 7.")]
ROWS = {m[1]: m[2] for m in re.finditer(r"^\| ([a-z_]+) \| [^|]+ \| ([^|]+) \|$", SECTION, re.M)}
DOCUMENTED = {table: set(re.findall(r"`((?:ix|uq)_\w+)", cell)) for table, cell in ROWS.items()}


@pytest.fixture
def db(tmp_path):
    engine = make_engine(f"sqlite:///{(tmp_path / 't.db').as_posix()}")
    Base.metadata.create_all(engine)
    return make_sessions(engine)


def index_names(table) -> set[str]:
    return {index.name for index in table.indexes}


def test_plan_section_6_is_parsed():
    assert len(DOCUMENTED) == 18
    assert DOCUMENTED["users"] == {"uq_users_email", "ix_users_created_at", "ix_users_deleted_at"}
    assert DOCUMENTED["rate_limits"] == {"ix_rate_limits_window_start"}


def test_every_table_is_documented_in_plan_section_6():
    assert set(Base.metadata.tables) <= set(DOCUMENTED)


def test_every_plan_section_6_table_exists():
    assert set(DOCUMENTED) <= set(Base.metadata.tables)


@pytest.mark.parametrize("name", sorted(models.__all__))
def test_every_documented_index_exists(name):
    table = getattr(models, name).__table__
    assert DOCUMENTED[table.name] <= index_names(table)


@pytest.mark.parametrize("name", sorted(models.__all__))
def test_every_foreign_key_column_leads_an_index(name):
    table = getattr(models, name).__table__
    leading = {next(iter(index.columns)).name for index in table.indexes if index.columns}
    leading.add(next(iter(table.primary_key.columns)).name)
    for fk in table.foreign_keys:
        assert fk.parent.name in leading, f"{table.name}.{fk.parent.name} has no index"


def user(email="salma@example.com", **kwargs):
    return models.User(email=email, password_hash="x", **kwargs)


def test_ids_are_uuidv7_and_sort_in_creation_order(db):
    with db.begin() as session:
        session.add_all([user(f"u{k}@example.com") for k in range(20)])
    with db() as session:
        rows = session.scalars(select(models.User).order_by(models.User.id)).all()
    assert [u.email for u in rows] == [f"u{k}@example.com" for k in range(20)]
    assert {u.id.version for u in rows} == {7}


def test_timestamps_round_trip_in_utc(db):
    riyadh = timezone(timedelta(hours=3))
    moment = datetime(2026, 11, 26, 15, 30, tzinfo=riyadh)
    with db.begin() as session:
        session.add(user(email_verified_at=moment))
    with db() as session:
        loaded = session.scalars(select(models.User)).one()
    assert loaded.email_verified_at == moment
    assert loaded.email_verified_at.tzinfo is UTC
    assert loaded.email_verified_at.hour == 12
    assert loaded.created_at.tzinfo is UTC


def test_a_naive_timestamp_is_refused(db):
    with pytest.raises(StatementError, match="timezone-aware"), db.begin() as session:
        session.add(user(email_verified_at=datetime(2026, 11, 26, 12)))


def test_emails_are_unique_ignoring_case(db):
    with db.begin() as session:
        session.add(user("Salma@Example.com"))
    with pytest.raises(IntegrityError), db.begin() as session:
        session.add(user("salma@example.COM"))


def test_a_user_is_in_a_workspace_once(db):
    with db.begin() as session:
        owner = user()
        session.add(owner)
        session.flush()
        space = models.Workspace(name="Salma", owner_id=owner.id, personal=True)
        session.add(space)
        session.flush()
        session.add(models.Membership(workspace_id=space.id, user_id=owner.id, role="owner"))
    with pytest.raises(IntegrityError), db.begin() as session:
        session.add(models.Membership(workspace_id=space.id, user_id=owner.id, role="admin"))


def test_foreign_keys_are_enforced(db):
    with pytest.raises(IntegrityError, match="FOREIGN KEY"), db.begin() as session:
        session.add(models.Workspace(name="x", owner_id=uuid7()))


def seeded(session):
    """A user, their workspace, a saved workflow version and a run of it."""
    owner = user()
    session.add(owner)
    session.flush()
    space = models.Workspace(name="Salma", owner_id=owner.id, personal=True)
    session.add(space)
    session.flush()
    flow = models.Workflow(workspace_id=space.id, name="Reconcile", created_by=owner.id)
    session.add(flow)
    session.flush()
    version = models.WorkflowVersion(workflow_id=flow.id, version=1, definition={},
                                     plan_hash="a" * 64)  # fmt: skip
    session.add(version)
    session.flush()
    run = models.Run(workspace_id=space.id, workflow_version_id=version.id, state="QUEUED",
                     plan_hash="a" * 64, idempotency_key="k1")  # fmt: skip
    session.add(run)
    session.flush()
    return space, flow, run


@pytest.mark.parametrize(
    "duplicate",
    [
        lambda s, space, flow, run: models.Run(workspace_id=space.id, state="QUEUED",
                                               plan_hash="a" * 64, idempotency_key="k1"),
        lambda s, space, flow, run: models.WorkflowVersion(workflow_id=flow.id, version=1,
                                                           definition={}, plan_hash="b" * 64),
        lambda s, space, flow, run: models.RunNode(run_id=run.id, node_id="a", state="DONE"),
        lambda s, space, flow, run: models.RunEvent(run_id=run.id, seq=1, type="x", payload={}),
    ],
    ids=["run idempotency key", "workflow version", "run node", "run event seq"],
)  # fmt: skip
def test_work_uniques_are_enforced(db, duplicate):
    with db.begin() as session:
        space, flow, run = seeded(session)
        session.add(models.RunNode(run_id=run.id, node_id="a", state="DONE"))
        session.add(models.RunEvent(run_id=run.id, seq=1, type="x", payload={}))
    with pytest.raises(IntegrityError), db.begin() as session:
        session.add(duplicate(session, space, flow, run))


def test_json_documents_round_trip(db):
    definition = {"nodes": [{"id": "a", "label": "رقم الطلب"}], "edges": []}
    with db.begin() as session:
        space, flow, run = seeded(session)
        session.add(models.WorkflowVersion(workflow_id=flow.id, version=2,
                                           definition=definition, plan_hash="c" * 64))  # fmt: skip
    with db() as session:
        stored = session.scalars(select(models.WorkflowVersion).where(
            models.WorkflowVersion.version == 2)).one()  # fmt: skip
    assert stored.definition == definition
