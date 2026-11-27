"""P8.1 templates and drafts, P8.9 `If-Match` on PATCH (T8.1, T8.9)."""

import json
import threading
from uuid import UUID

import pytest
from sqlalchemy.orm.exc import StaleDataError
from web import signed_in, upload

from app.db import models as m
from app.db.engine import make_engine, make_sessions

ORDERS = b"order_id,amount\nO-101,100\nO-102,200\n"
PAYMENTS = json.dumps([{"order_id": "O-101", "amount": 100}]).encode()


@pytest.fixture
def web(db_url, tmp_path):
    return signed_in(db_url, tmp_path)


def create(web, *names_and_data, template="reconcile"):
    ids = [upload(web, name, data)["id"] for name, data in names_and_data]
    body = {"file_ids": ids, "planner": "template", "template_id": template}
    return web.post(f"/api/v1/workspaces/{web.ws}/drafts", json=body)


def draft_url(web, draft):
    return f"/api/v1/workspaces/{web.ws}/drafts/{draft['id']}"


def test_templates_list_both_with_their_inputs(web):
    response = web.get("/api/v1/templates")

    assert response.status_code == 200
    reconcile = {t["id"]: t for t in response.json()}["reconcile"]
    assert [i["title_key"] for i in reconcile["required_inputs"]] == [
        "templates.reconcile.inputs.0", "templates.reconcile.inputs.1"]  # fmt: skip


def test_a_reconcile_draft_is_planned_from_the_files_columns(web):
    response = create(web, ("orders.csv", ORDERS), ("payments.json", PAYMENTS))

    assert response.status_code == 201
    draft = response.json()
    assert response.headers["ETag"] == f'"{draft["plan_hash"]}"'
    assert draft["validation"] == {"valid": True, "errors": [], "warnings": []}
    assert draft["explanation"]["key"].startswith("plans.")
    assert draft["ai_disclosure"] == {"sent_fields": [], "samples_sent": False}
    compare = next(n for n in draft["definition"]["nodes"] if n["id"] == "compare")
    assert compare["params"]["key"] == "order_id"


def test_get_returns_the_same_draft_and_etag(web):
    draft = create(web, ("orders.csv", ORDERS), ("payments.json", PAYMENTS)).json()

    response = web.get(draft_url(web, draft))

    assert response.json() == draft
    assert response.headers["ETag"] == f'"{draft["plan_hash"]}"'


@pytest.mark.parametrize(("template", "code"), [(None, "MISSING"), ("nope", "INVALID")])
def test_the_template_planner_needs_a_known_template(web, template, code):
    response = create(web, ("orders.csv", ORDERS), ("payments.json", PAYMENTS), template=template)

    assert response.status_code == 422
    assert response.json()["errors"] == [{"path": "body.template_id", "code": code, "params": {}}]


def test_a_reconcile_needs_exactly_two_files(web):
    response = create(web, ("orders.csv", ORDERS))

    assert response.status_code == 422
    assert response.json()["errors"][0]["path"] == "body.file_ids"


def test_an_unreadable_file_gives_its_operation_code(web):
    response = create(web, ("orders.csv", ORDERS), ("bad.csv", b"a,a\n1,2\n"))

    assert response.status_code == 422
    error = response.json()["errors"][0]
    assert (error["path"], error["code"]) == ("body.file_ids.1", "CSV_DUPLICATE_HEADER")
    assert error["params"] == {"columns": ["a"]}


def test_a_file_from_another_workspace_is_not_found(web, db_url, tmp_path):
    other = signed_in(db_url, tmp_path / "other", email="o@example.com")
    foreign = upload(other, "orders.csv", ORDERS)["id"]
    mine = upload(web, "payments.json", PAYMENTS)["id"]

    body = {"file_ids": [mine, foreign], "planner": "template", "template_id": "reconcile"}
    response = web.post(f"/api/v1/workspaces/{web.ws}/drafts", json=body)

    assert response.status_code == 404


def test_the_ai_planner_is_not_implemented_yet(web):
    mine = upload(web, "orders.csv", ORDERS)["id"]
    body = {"file_ids": [mine], "planner": "ai", "prompt": "compare"}

    assert web.post(f"/api/v1/workspaces/{web.ws}/drafts", json=body).status_code == 501


def edited(draft, key="amount"):
    definition = json.loads(json.dumps(draft["definition"]))
    next(n for n in definition["nodes"] if n["id"] == "compare")["params"]["key"] = key
    return {"definition": definition}


def test_patch_revalidates_and_gives_a_new_plan_hash(web):
    draft = create(web, ("orders.csv", ORDERS), ("payments.json", PAYMENTS)).json()

    response = web.patch(draft_url(web, draft), json=edited(draft),
                         headers={"If-Match": f'"{draft["plan_hash"]}"'})  # fmt: skip

    assert response.status_code == 200
    assert response.json()["plan_hash"] != draft["plan_hash"]
    assert response.headers["ETag"] == f'"{response.json()["plan_hash"]}"'


def test_patch_without_if_match_is_428_and_a_stale_one_412(web):
    draft = create(web, ("orders.csv", ORDERS), ("payments.json", PAYMENTS)).json()

    missing = web.patch(draft_url(web, draft), json=edited(draft))
    stale = web.patch(draft_url(web, draft), json=edited(draft), headers={"If-Match": '"0"'})

    assert (missing.status_code, missing.json()["code"]) == (428, "PRECONDITION_REQUIRED")
    assert (stale.status_code, stale.json()["code"]) == (412, "PRECONDITION_FAILED")


def test_of_two_edits_from_the_same_version_exactly_one_wins(web):
    draft = create(web, ("orders.csv", ORDERS), ("payments.json", PAYMENTS)).json()
    etag = {"If-Match": f'"{draft["plan_hash"]}"'}
    statuses = []

    def edit(key):
        statuses.append(web.patch(draft_url(web, draft), json=edited(draft, key),
                                  headers=etag).status_code)  # fmt: skip

    threads = [threading.Thread(target=edit, args=(k,)) for k in ("amount", "paid")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(statuses) == [200, 412]


def test_a_write_from_a_stale_read_is_refused(web, db_url):
    """The race itself: both sessions read version 1, so only the first write may land."""
    draft = create(web, ("orders.csv", ORDERS), ("payments.json", PAYMENTS)).json()
    sessions = make_sessions(make_engine(db_url))
    first, second = sessions(), sessions()
    rows = [s.get(m.Draft, UUID(draft["id"])) for s in (first, second)]
    for row, new in zip(rows, ("a" * 64, "b" * 64), strict=True):
        row.plan_hash = new
    first.commit()

    with pytest.raises(StaleDataError):
        second.commit()
