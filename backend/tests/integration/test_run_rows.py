"""P8.1 run rows: a run pins its definition, and its events are numbered 1, 2, …"""

from datetime import UTC, datetime

import pytest
from fakes import PIPELINE
from sqlalchemy import select

from app.core.draft import Explanation, WorkflowDraft
from app.core.engine.run import new_run
from app.db import models as m
from app.db.base import Base
from app.db.engine import make_engine, make_sessions
from app.db.engine_state import apply, load_run
from app.db.run_events import emit

NOW = datetime(2026, 11, 27, 12, tzinfo=UTC)


@pytest.fixture
def sessions(db_url):
    Base.metadata.create_all(make_engine(db_url))
    return make_sessions(make_engine(db_url))


def test_a_run_from_a_draft_keeps_its_definition_after_the_draft_changes(sessions):
    run = new_run(PIPELINE, NOW)
    with sessions.begin() as session:
        owner = m.User(email="r@example.com", password_hash="x")
        session.add(owner)
        session.flush()
        ws = m.Workspace(name="r", owner_id=owner.id)
        session.add(ws)
        session.flush()
        drafted = WorkflowDraft(definition=PIPELINE, explanation=Explanation(key="k"))
        draft = m.Draft(workspace_id=ws.id, plan_hash=run.plan_hash, planner="template",
                        draft=drafted.model_dump(mode="json"))  # fmt: skip
        session.add(draft)
        session.flush()
        row = m.Run(id=run.id, workspace_id=ws.id, draft_id=draft.id, plan_hash=run.plan_hash,
                    definition=PIPELINE.model_dump(mode="json"), created_at=NOW)  # fmt: skip
        apply(row, run)
        session.add(row)
        session.flush()
        draft.draft = {**draft.draft, "definition": {**draft.draft["definition"], "nodes": []}}
        for _ in range(3):
            emit(session, row.id, "state_changed", NOW, state=row.state)

    with sessions() as session:
        assert load_run(session, ws.id, run.id).definition == PIPELINE
        events = session.scalars(select(m.RunEvent).order_by(m.RunEvent.seq)).all()
        assert [(e.seq, e.payload) for e in events] == [(n, {"state": "DRAFT"}) for n in (1, 2, 3)]
