"""P8.2 and P8.3 the job worker: one node per job, resumable after a crash (T8.6)."""

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from web import signed_in, upload

from app.api.v1.run_models import RunEvents
from app.db import models as m
from app.db.jobs import claim
from app.worker import LEASE, work_once

ORDERS = b"order_id,amount\nO-101,100\nO-102,200\nO-103,300\n"
PAYMENTS = json.dumps([{"order_id": "O-101", "amount": 100}, {"order_id": "O-102", "amount": 190},
                       {"order_id": "O-104", "amount": 50}]).encode()  # fmt: skip


@pytest.fixture
def web(db_url, tmp_path):
    return signed_in(db_url, tmp_path)


def approved_run(web):
    ids = [upload(web, "orders.csv", ORDERS)["id"], upload(web, "payments.json", PAYMENTS)["id"]]
    body = {"file_ids": ids, "planner": "template", "template_id": "reconcile"}
    draft = web.post(f"/api/v1/workspaces/{web.ws}/drafts", json=body).json()
    run = web.post(f"/api/v1/workspaces/{web.ws}/runs", json={"draft_id": draft["id"]},
                   headers={"Idempotency-Key": str(uuid4())}).json()  # fmt: skip
    key = {"Idempotency-Key": str(uuid4())}
    web.post(f"/api/v1/workspaces/{web.ws}/runs/{run['id']}/approve",
             json={"plan_hash": run["plan_hash"]}, headers=key)  # fmt: skip
    return run


def drain(web, clock=lambda: datetime.now(UTC)) -> int:
    count = 0
    while work_once(web.app.state.sessions, web.app.state.storage, clock):
        count += 1
    return count


def get(web, run, path=""):
    return web.get(f"/api/v1/workspaces/{web.ws}/runs/{run['id']}{path}").json()


def test_each_node_is_its_own_job_and_the_run_succeeds(web):
    run = approved_run(web)

    jobs = drain(web)

    done = get(web, run)
    assert done["state"] == "SUCCEEDED" and done["finished_at"] is not None
    assert sorted(n["node_id"] for n in done["nodes"]) == ["compare", "left", "report", "right"]
    assert jobs == len(done["nodes"]) + 1  # one per node, then the one that ends the run


def test_the_events_trace_the_run(web):
    run = approved_run(web)
    drain(web)

    events = get(web, run, "/events")["events"]

    assert [(e["type"], e["node_id"] or e["payload"].get("state")) for e in events] == [
        ("state_changed", "AWAITING_APPROVAL"), ("state_changed", "QUEUED"),
        ("state_changed", "RUNNING"), ("node_finished", "left"), ("node_finished", "right"),
        ("node_finished", "compare"), ("node_finished", "report"),
        ("state_changed", "SUCCEEDED"),
    ]  # fmt: skip
    parsed = RunEvents.model_validate(get(web, run, "/events")).events
    assert [e.seq for e in parsed] == list(range(1, len(events) + 1))
    assert {type(e.payload).__name__ for e in parsed} == {
        "StateChangedPayload", "NodeFinishedPayload",
    }  # fmt: skip


def test_a_job_whose_worker_died_is_done_by_another_after_the_lease(web):
    run = approved_run(web)
    start = datetime.now(UTC)
    claim(web.app.state.sessions, start, LEASE)  # this worker dies before running the step

    assert drain(web, clock=lambda: start) == 0  # the job is still leased
    drain(web, clock=lambda: start + LEASE * 2)

    assert get(web, run)["state"] == "SUCCEEDED"


def test_a_run_cancelled_before_it_starts_is_cancelled_by_the_worker(web):
    run = approved_run(web)
    web.post(f"/api/v1/workspaces/{web.ws}/runs/{run['id']}/cancel")

    drain(web)

    assert get(web, run)["state"] == "CANCELLED"
    assert get(web, run)["nodes"] == []


def test_the_inputs_are_stored_once_for_the_whole_run(web):
    run = approved_run(web)
    drain(web)

    with web.app.state.sessions() as session:
        inputs = session.scalars(select(m.Artifact).where(
            m.Artifact.run_id == UUID(run["id"]), m.Artifact.node_id.is_(None))).all()  # fmt: skip
    assert sorted(a.source["file"] for a in inputs) == ["orders.csv", "payments.json"]
