"""P8.2 housekeeping, the worker's scheduled jobs: approval expiry, file retention (P6.6) and
account purge (P5.10) run without anyone opening the run, the file or the account."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from web import signed_in, upload

from app.db import models as m
from app.housekeeping import housekeep

ORDERS = b"order_id,amount\nO-1,10\n"


@pytest.fixture
def web(db_url, tmp_path):
    return signed_in(db_url, tmp_path)


def waiting_run(web) -> dict:
    ids = [upload(web, "a.csv", ORDERS)["id"], upload(web, "b.csv", ORDERS)["id"]]
    body = {"file_ids": ids, "planner": "template", "template_id": "reconcile"}
    draft = web.post(f"/api/v1/workspaces/{web.ws}/drafts", json=body).json()
    return web.post(f"/api/v1/workspaces/{web.ws}/runs", json={"draft_id": draft["id"]},
                    headers={"Idempotency-Key": str(uuid4())}).json()  # fmt: skip


def run(web, run_id: str, path: str = "") -> dict:
    return web.get(f"/api/v1/workspaces/{web.ws}/runs/{run_id}{path}").json()


def sweep(web, now: datetime) -> dict[str, int]:
    app = web.app
    return housekeep(app.state.sessions, app.state.storage, app.state.settings, now)


def test_a_run_nobody_approved_expires_with_its_event(web):
    stale = waiting_run(web)
    ttl = web.app.state.settings.approval_ttl

    assert sweep(web, datetime.now(UTC) + ttl - timedelta(minutes=1))["expired_runs"] == 0
    assert sweep(web, datetime.now(UTC) + ttl + timedelta(minutes=1))["expired_runs"] == 1

    assert run(web, stale["id"])["state"] == "EXPIRED"
    last = run(web, stale["id"], "/events")["events"][-1]
    assert (last["type"], last["payload"]) == ("state_changed", {"state": "EXPIRED"})


def test_expired_files_and_deleted_accounts_are_purged(web):
    file_id = upload(web, "old.csv", ORDERS)["id"]
    later = datetime.now(UTC) + timedelta(days=400)

    counts = sweep(web, later)

    assert counts["purged_files"] == 1
    assert counts["purged_users"] == 0
    with web.app.state.sessions() as session:
        assert session.get(m.File, UUID(file_id)) is None
