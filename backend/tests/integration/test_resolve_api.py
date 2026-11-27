"""§7 resolve: a run that stops for review is answered, approved again and finishes (T8.1)."""

import json
from uuid import uuid4

import pytest
from web import signed_in, upload

from app.worker import work_once

ORDERS = b"order_id,amount,paid_on\nO-1,100,03/04/2026\n"
PAYMENTS = json.dumps([{"order_id": "O-1", "amount": 100}]).encode()


@pytest.fixture
def web(db_url, tmp_path):
    return signed_in(db_url, tmp_path)


def key():
    return {"Idempotency-Key": str(uuid4())}


def with_dates(definition: dict) -> dict:
    """The reconcile plan with a `normalize` of the orders' `paid_on` dates before `compare`."""
    definition["nodes"].append({"id": "left_clean", "operation": {"id": "normalize", "version": 1},
                                "params": {"key": "order_id", "dates": ["paid_on"]}})  # fmt: skip
    for edge in definition["edges"]:
        if edge["target"] == {"node_id": "compare", "port": "left"}:
            edge["target"] = {"node_id": "left_clean", "port": "table"}
    definition["edges"].append({"source": {"node_id": "left_clean", "port": "table"},
                                "target": {"node_id": "compare", "port": "left"}})  # fmt: skip
    return definition


def drain(web):
    while work_once(web.app.state.sessions, web.app.state.storage):
        pass


def url(web, run, path=""):
    return f"/api/v1/workspaces/{web.ws}/runs/{run['id']}{path}"


@pytest.fixture
def review(web):
    """A run stopped in NEEDS_REVIEW because `03/04/2026` could be day-first or month-first."""
    ids = [upload(web, "orders.csv", ORDERS)["id"], upload(web, "payments.json", PAYMENTS)["id"]]
    drafts = f"/api/v1/workspaces/{web.ws}/drafts"
    draft = web.post(drafts, json={"file_ids": ids, "planner": "template",
                                   "template_id": "reconcile"}).json()  # fmt: skip
    edit = {"definition": with_dates(draft["definition"])}
    draft = web.patch(f"{drafts}/{draft['id']}", json=edit,
                      headers={"If-Match": f'"{draft["plan_hash"]}"'}).json()  # fmt: skip
    run = web.post(f"/api/v1/workspaces/{web.ws}/runs", json={"draft_id": draft["id"]},
                   headers=key()).json()  # fmt: skip
    web.post(url(web, run, "/approve"), json={"plan_hash": run["plan_hash"]}, headers=key())
    drain(web)
    return web.get(url(web, run)).json()


def test_the_run_asks_which_date_order(review):
    [question] = review["review_issues"]

    assert review["state"] == "NEEDS_REVIEW"
    assert (question["code"], question["node_id"]) == ("DATE_AMBIGUOUS", "left_clean")
    assert question["params"] == {"column": "paid_on", "options": ["DMY", "MDY"]}


def test_an_answer_gives_a_new_plan_to_approve_and_the_run_finishes(web, review):
    [question] = review["review_issues"]
    choice = {"code": question["code"], "path": question["path"], "value": "DMY"}

    resolved = web.post(url(web, review, "/resolve"), headers=key(),
                        json={"plan_hash": review["plan_hash"], "choices": [choice]})  # fmt: skip

    run = resolved.json()
    assert (resolved.status_code, run["state"]) == (200, "AWAITING_APPROVAL")
    assert run["plan_hash"] != review["plan_hash"] and run["nodes"] == []
    clean = next(n for n in run["definition"]["nodes"] if n["id"] == "left_clean")
    assert clean["params"]["date_order"] == "DMY"
    web.post(url(web, run, "/approve"), json={"plan_hash": run["plan_hash"]}, headers=key())
    drain(web)
    assert web.get(url(web, run)).json()["state"] == "SUCCEEDED"


def test_a_retried_answer_gives_the_same_run(web, review):
    [question] = review["review_issues"]
    choice = {"code": question["code"], "path": question["path"], "value": "MDY"}
    body = {"plan_hash": review["plan_hash"], "choices": [choice]}
    same = key()

    first = web.post(url(web, review, "/resolve"), headers=same, json=body).json()
    again = web.post(url(web, review, "/resolve"), headers=same, json=body)

    assert (again.status_code, again.json()["plan_hash"]) == (200, first["plan_hash"])


def test_an_answer_that_is_not_an_option_is_a_field_error(web, review):
    [question] = review["review_issues"]
    choice = {"code": question["code"], "path": question["path"], "value": "YMD"}

    response = web.post(url(web, review, "/resolve"), headers=key(),
                        json={"plan_hash": review["plan_hash"], "choices": [choice]})  # fmt: skip

    assert response.status_code == 422
    assert response.json()["errors"][0]["path"] == "body.choices.0"


def test_resolve_needs_the_reviewed_plan_and_the_review_state(web, review):
    [question] = review["review_issues"]
    choice = {"code": question["code"], "path": question["path"], "value": "DMY"}

    stale = web.post(url(web, review, "/resolve"), headers=key(),
                     json={"plan_hash": "0" * 64, "choices": [choice]})  # fmt: skip
    web.post(url(web, review, "/cancel"))
    late = web.post(url(web, review, "/resolve"), headers=key(),
                    json={"plan_hash": review["plan_hash"], "choices": [choice]})  # fmt: skip

    assert stale.json()["code"] == "PLAN_HASH_MISMATCH"
    assert late.json()["errors"][0]["params"] == {"from": "CANCELLED", "action": "resolve"}
