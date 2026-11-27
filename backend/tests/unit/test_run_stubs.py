"""P0.5: the §7 runs lifecycle is documented in OpenAPI. The behaviour is in
`tests/integration/test_runs_api.py` (P8.1); `resolve`, list, events and runs from
a workflow are still 501."""

import pytest

UUID = "01937a5e-7f00-7000-8000-000000000001"
IDS = {"ws_id": UUID, "run_id": UUID}
RUNS = "/api/v1/workspaces/{ws_id}/runs"
RUN = f"{RUNS}/{{run_id}}"
PROBLEM = {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}}
IDEMPOTENT = {"Idempotency-Key": UUID}
FROM_DRAFT = {"draft_id": UUID}
FROM_WORKFLOW = {"workflow_id": UUID, "version": 1, "file_ids": [UUID]}
APPROVE = {"plan_hash": "a" * 64}
RESOLVE = APPROVE | {"choices": [{"code": "DATE_AMBIGUOUS", "path": "nodes/0", "value": "DMY"}]}
STATES = {
    "DRAFT", "VALIDATED", "AWAITING_APPROVAL", "QUEUED", "RUNNING", "NEEDS_REVIEW", "SUCCEEDED",
    "PARTIAL", "FAILED", "CANCEL_REQUESTED", "CANCELLED", "EXPIRED",
}  # fmt: skip

# (method, OpenAPI path, success status, sample valid body, operationId) — api_contract.md §7.
ENDPOINTS = [
    ("post", RUNS, 201, FROM_DRAFT, "runs_create"),
    ("post", f"{RUN}/approve", 202, APPROVE, "runs_approve"),
    ("post", f"{RUN}/resolve", 200, RESOLVE, "runs_resolve"),
    ("post", f"{RUN}/cancel", 202, None, "runs_cancel"),
    ("get", RUNS, 200, None, "runs_list"),
    ("get", RUN, 200, None, "runs_get"),
    ("get", f"{RUN}/events", 200, None, "runs_events"),
]


def operation(openapi: dict, method: str, path: str) -> dict:
    return openapi["paths"][path][method]


@pytest.mark.parametrize(("method", "path", "status", "body", "operation_id"), ENDPOINTS)
def test_endpoint_is_documented(openapi, method, path, status, body, operation_id):
    documented = operation(openapi, method, path)

    assert str(status) in documented["responses"]
    assert documented["operationId"] == operation_id
    for error in ("401", "403", "404", "409", "422", "429", "501"):
        assert documented["responses"][error]["content"] == PROBLEM


@pytest.mark.parametrize(
    ("method", "path", "status", "body", "operation_id"),
    [e for e in ENDPOINTS if e[4] in {"runs_resolve", "runs_list", "runs_events"}],
)
def test_the_rest_are_still_501_stubs(client, method, path, status, body, operation_id):
    response = client.request(method, path.format(**IDS), json=body, headers=IDEMPOTENT)

    assert response.status_code == 501
    assert response.json()["code"] == "NOT_IMPLEMENTED"


def test_lifecycle_paths_are_all_documented(openapi):
    documented = {
        (method, path)
        for path, operations in openapi["paths"].items()
        if path.startswith(RUNS) and "/outputs" not in path
        for method in operations
    }

    assert documented == {(method, path) for method, path, *_ in ENDPOINTS}


@pytest.mark.parametrize(
    ("path", "body"), [(RUNS, FROM_DRAFT), (f"{RUN}/approve", APPROVE), (f"{RUN}/resolve", RESOLVE)]
)
def test_state_changing_actions_require_an_idempotency_key(client, openapi, path, body):
    response = client.post(path.format(**IDS), json=body)
    header = next(
        param
        for param in operation(openapi, "post", path)["parameters"]
        if param["name"] == "Idempotency-Key"
    )

    assert header["in"] == "header"
    assert header["required"] is True
    assert [(error["path"], error["code"]) for error in response.json()["errors"]] == [
        ("header.Idempotency-Key", "MISSING")
    ]


def test_cancel_takes_no_idempotency_key(openapi):
    names = {param["name"] for param in operation(openapi, "post", f"{RUN}/cancel")["parameters"]}

    assert "Idempotency-Key" not in names


def test_a_run_starts_from_a_draft_or_a_saved_workflow(client):
    url = RUNS.format(**IDS)

    assert client.post(url, json=FROM_WORKFLOW, headers=IDEMPOTENT).status_code == 501
    assert client.post(url, json=FROM_DRAFT | FROM_WORKFLOW, headers=IDEMPOTENT).status_code == 422
    assert client.post(url, json={}, headers=IDEMPOTENT).status_code == 422


@pytest.mark.parametrize("plan_hash", ["a" * 63, "A" * 64, "g" * 64])
def test_approve_needs_a_sha256_plan_hash(client, plan_hash):
    url = f"{RUN}/approve".format(**IDS)

    assert client.post(url, json={"plan_hash": plan_hash}, headers=IDEMPOTENT).status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {"choices": RESOLVE["choices"]},
        APPROVE,
        APPROVE | {"choices": []},
        APPROVE | {"choices": [{"code": "DATE_AMBIGUOUS", "path": "nodes/0"}]},
    ],
)
def test_resolve_needs_the_reviewed_plan_hash_and_one_choice_or_more(client, body):
    url = f"{RUN}/resolve".format(**IDS)

    assert client.post(url, json=body, headers=IDEMPOTENT).status_code == 422


def test_list_is_a_cursor_page_filtered_by_state(client, openapi, schemas):
    listing = operation(openapi, "get", RUNS)

    assert {"cursor", "limit", "state"} <= {param["name"] for param in listing["parameters"]}
    assert set(schemas["RunSummaryPage"]["properties"]) == {"items", "next_cursor"}
    assert client.get(RUNS.format(**IDS), params={"state": "DONE"}).status_code == 422


def test_events_poll_after_a_sequence_number(client, schemas):
    url = f"{RUN}/events".format(**IDS)

    assert set(schemas["RunEvents"]["properties"]) == {"events", "last_seq"}
    assert client.get(url, params={"after": -1}).status_code == 422


def test_run_schemas_match_contract(schemas):
    assert set(schemas["RunState"]["enum"]) == STATES
    assert set(schemas["Run"]["properties"]) == {
        "id", "state", "plan_hash", "definition", "nodes", "summary", "approved_by",
        "approved_at", "approval_expires_at", "created_at", "finished_at", "review_issues",
    }  # fmt: skip
    expires = schemas["Run"]["properties"]["approval_expires_at"]
    assert {kind.get("type") for kind in expires["anyOf"]} == {"string", "null"}
    assert "approval_expires_at" not in schemas["Run"].get("required", [])
    assert set(schemas["ResolveRequest"]["properties"]) == {"plan_hash", "choices"}
    assert set(schemas["ReviewChoice"]["properties"]) == {"code", "path", "value"}
    assert set(schemas["RunNode"]["properties"]) == {
        "node_id", "operation_id", "state", "attempt", "started_at", "finished_at", "error_code",
        "warnings",
    }  # fmt: skip
    assert set(schemas["RunCounts"]["properties"]) == {
        "matched", "value_diff", "missing_left", "missing_right",
    }  # fmt: skip
    assert set(schemas["RunSummary"]["properties"]) == {
        "id", "state", "title", "created_at", "finished_at", "summary",
    }  # fmt: skip
    assert set(schemas["RunEvent"]["properties"]) == {
        "seq", "type", "node_id", "payload", "created_at",
    }  # fmt: skip
    assert schemas["RunEvent"]["properties"]["type"]["enum"] == [
        "state_changed", "node_started", "node_finished", "warning",
    ]  # fmt: skip
