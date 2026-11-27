"""P8.1 runs: create, approve, cancel, get, list and events; P8.4 Idempotency-Key (T8.1, T8.3,
T8.5, T8.7)."""

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from web import signed_in, upload

from app.db import models as m
from app.db.engine import make_engine, make_sessions

ORDERS = b"order_id,amount\nO-101,100\nO-102,200\n"
PAYMENTS = json.dumps([{"order_id": "O-101", "amount": 100}]).encode()


@pytest.fixture
def web(db_url, tmp_path):
    client = signed_in(db_url, tmp_path)
    client.db_url = db_url
    return client


def make_draft(web):
    ids = [upload(web, "orders.csv", ORDERS)["id"], upload(web, "payments.json", PAYMENTS)["id"]]
    body = {"file_ids": ids, "planner": "template", "template_id": "reconcile"}
    return web.post(f"/api/v1/workspaces/{web.ws}/drafts", json=body).json()


def runs(web, path=""):
    return f"/api/v1/workspaces/{web.ws}/runs{path}"


def start(web, draft, key=None):
    headers = {"Idempotency-Key": key or str(uuid4())}
    return web.post(runs(web), json={"draft_id": draft["id"]}, headers=headers)


def approve(web, run, plan_hash=None, key=None):
    headers = {"Idempotency-Key": key or str(uuid4())}
    return web.post(runs(web, f"/{run['id']}/approve"), headers=headers,
                    json={"plan_hash": plan_hash or run["plan_hash"]})  # fmt: skip


def run_count(web):
    with make_sessions(make_engine(web.db_url))() as session:
        return len(session.scalars(select(m.Run)).all())


def jobs(web):
    with make_sessions(make_engine(web.db_url))() as session:
        return session.scalars(select(m.Job)).all()


def test_a_run_from_a_valid_draft_waits_for_approval(web):
    draft = make_draft(web)

    response = start(web, draft)

    assert response.status_code == 201
    run = response.json()
    assert (run["state"], run["plan_hash"]) == ("AWAITING_APPROVAL", draft["plan_hash"])
    assert run["definition"] == draft["definition"] and run["nodes"] == []
    assert run["approval_expires_at"] is not None


def test_the_same_key_gives_the_same_run_and_another_body_409(web):
    draft, other, key = make_draft(web), make_draft(web), str(uuid4())

    first, again = start(web, draft, key).json(), start(web, draft, key)
    clash = start(web, other, key)

    assert (again.status_code, again.json()["id"]) == (201, first["id"])
    assert (clash.status_code, clash.json()["code"]) == (409, "IDEMPOTENCY_KEY_MISMATCH")
    assert run_count(web) == 1


def test_a_missing_key_is_a_field_error(web):
    response = web.post(runs(web), json={"draft_id": make_draft(web)["id"]})

    assert response.status_code == 422
    assert response.json()["errors"][0]["path"] == "header.Idempotency-Key"


def test_an_invalid_draft_is_refused_with_its_issues(web):
    draft = make_draft(web)
    definition = draft["definition"]
    next(n for n in definition["nodes"] if n["id"] == "compare")["params"] = {}
    web.patch(f"/api/v1/workspaces/{web.ws}/drafts/{draft['id']}", json={"definition": definition},
              headers={"If-Match": f'"{draft["plan_hash"]}"'})  # fmt: skip

    response = start(web, draft)

    assert (response.status_code, response.json()["code"]) == (422, "DRAFT_INVALID")
    assert response.json()["errors"] and run_count(web) == 0


def test_the_run_keeps_its_plan_when_the_draft_is_edited(web):
    draft = make_draft(web)
    run = start(web, draft).json()
    definition = json.loads(json.dumps(draft["definition"]))
    next(n for n in definition["nodes"] if n["id"] == "compare")["params"]["key"] = "amount"
    web.patch(f"/api/v1/workspaces/{web.ws}/drafts/{draft['id']}", json={"definition": definition},
              headers={"If-Match": f'"{draft["plan_hash"]}"'})  # fmt: skip

    assert web.get(runs(web, f"/{run['id']}")).json()["definition"] == draft["definition"]


def test_approve_queues_the_run_for_the_worker(web):
    run = start(web, make_draft(web)).json()

    response = approve(web, run)

    assert response.status_code == 202
    assert (response.json()["state"], response.json()["approval_expires_at"]) == ("QUEUED", None)
    assert [(j.kind, j.payload["run_id"]) for j in jobs(web)] == [("run_step", run["id"])]


def test_approve_needs_the_plan_that_was_shown(web):
    run = start(web, make_draft(web)).json()

    response = approve(web, run, plan_hash="0" * 64)

    assert (response.status_code, response.json()["code"]) == (409, "PLAN_HASH_MISMATCH")
    assert web.get(runs(web, f"/{run['id']}")).json()["state"] == "AWAITING_APPROVAL"


def test_a_retried_approve_answers_the_same_and_a_second_one_is_409(web):
    run, key = start(web, make_draft(web)).json(), str(uuid4())
    approve(web, run, key=key)

    retry = approve(web, run, key=key)
    clash = approve(web, run, plan_hash="1" * 64, key=key)
    second = approve(web, run)

    assert (retry.status_code, retry.json()["state"]) == (202, "QUEUED")
    assert clash.json()["code"] == "IDEMPOTENCY_KEY_MISMATCH"
    assert second.status_code == 409
    assert second.json()["errors"][0]["params"] == {"from": "QUEUED", "action": "approve"}
    assert len(jobs(web)) == 1


def test_an_approval_after_the_deadline_is_refused(web):
    run = start(web, make_draft(web)).json()
    with make_sessions(make_engine(web.db_url)).begin() as session:
        row = session.get(m.Run, UUID(run["id"]))
        row.state_since = datetime.now(UTC) - timedelta(hours=25)

    response = approve(web, run)

    assert response.status_code == 409
    assert response.json()["errors"][0]["params"] == {"from": "EXPIRED", "action": "approve"}


def test_cancel_before_approval_asks_the_worker_to_stop_it(web):
    run = start(web, make_draft(web)).json()

    response = web.post(runs(web, f"/{run['id']}/cancel"))

    assert (response.status_code, response.json()["state"]) == (202, "CANCEL_REQUESTED")
    assert [j.kind for j in jobs(web)] == ["run_step"]


def test_another_workspaces_run_is_not_found(web, db_url, tmp_path):
    run = start(web, make_draft(web)).json()
    other = signed_in(db_url, tmp_path / "other", email="o@example.com")

    assert other.get(f"/api/v1/workspaces/{web.ws}/runs/{run['id']}").status_code == 404
    assert other.get(f"/api/v1/workspaces/{other.ws}/runs/{run['id']}").status_code == 404
