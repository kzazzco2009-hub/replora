"""P0.5: the §8 workflows and replay contract is served as 501 stubs and documented in OpenAPI."""

import pytest

UUID = "01937a5e-7f00-7000-8000-000000000001"
IDS = {"ws_id": UUID, "workflow_id": UUID, "version": 1}
WORKFLOWS = "/api/v1/workspaces/{ws_id}/workflows"
WORKFLOW = f"{WORKFLOWS}/{{workflow_id}}"
PROBLEM = {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}}
CREATE = {"name": "Monthly bank reconciliation", "draft_id": UUID}
REPLAY = {"file_ids": [UUID]}
NEW_VERSION = {"base_version": 1, "mapping": {"Amount": "Total"}}

# (method, OpenAPI path, success status, sample valid body, operationId) — api_contract.md §8.
ENDPOINTS = [
    ("post", WORKFLOWS, 201, CREATE, "workflows_create"),
    ("get", WORKFLOWS, 200, None, "workflows_list"),
    ("get", WORKFLOW, 200, None, "workflows_get"),
    ("get", f"{WORKFLOW}/versions/{{version}}", 200, None, "workflows_get_version"),
    ("post", f"{WORKFLOW}/replay-check", 200, REPLAY, "workflows_replay_check"),
    ("post", f"{WORKFLOW}/versions", 201, NEW_VERSION, "workflows_create_version"),
    ("delete", WORKFLOW, 204, None, "workflows_delete"),
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


@pytest.mark.parametrize(("method", "path", "status", "body", "operation_id"), ENDPOINTS)
def test_stub_answers_501_problem_json(client, method, path, status, body, operation_id):
    response = client.request(method, path.format(**IDS), json=body)

    assert response.status_code == 501
    assert response.json()["code"] == "NOT_IMPLEMENTED"


def test_all_contract_paths_and_nothing_else(openapi):
    documented = {
        (method, path)
        for path, operations in openapi["paths"].items()
        if path.startswith(WORKFLOWS)
        for method in operations
    }

    assert documented == {(method, path) for method, path, *_ in ENDPOINTS}


BODY_ERRORS = [
    (WORKFLOWS, CREATE | {"name": ""}, "body.name", "STRING_TOO_SHORT"),
    (WORKFLOWS, CREATE | {"name": "x" * 101}, "body.name", "STRING_TOO_LONG"),
    (f"{WORKFLOW}/replay-check", {"file_ids": []}, "body.file_ids", "TOO_SHORT"),
    (f"{WORKFLOW}/versions", NEW_VERSION | {"base_version": 0}, "body.base_version",
     "GREATER_THAN_EQUAL"),
]  # fmt: skip


@pytest.mark.parametrize(("path", "body", "error_path", "code"), BODY_ERRORS)
def test_body_limits(client, path, body, error_path, code):
    response = client.post(path.format(**IDS), json=body)

    assert response.status_code == 422
    assert [(error["path"], error["code"]) for error in response.json()["errors"]] == [
        (error_path, code)
    ]


def test_version_in_the_path_starts_at_1(client):
    assert client.get(f"{WORKFLOW}/versions/0".format(**IDS)).status_code == 422


def test_list_is_a_cursor_page_with_a_name_search(openapi, schemas):
    names = {param["name"] for param in operation(openapi, "get", WORKFLOWS)["parameters"]}

    assert {"cursor", "limit", "q"} <= names
    assert set(schemas["WorkflowPage"]["properties"]) == {"items", "next_cursor"}


def test_workflow_schemas_match_contract(schemas):
    workflow = {"id", "name", "latest_version", "created_by", "created_at"}

    assert set(schemas["Workflow"]["properties"]) == workflow
    assert set(schemas["WorkflowDetail"]["properties"]) == workflow | {"versions"}
    assert set(schemas["WorkflowVersionInfo"]["properties"]) == {
        "version",
        "plan_hash",
        "created_at",
    }
    assert set(schemas["WorkflowVersion"]["properties"]) == {
        "workflow_id", "version", "definition", "plan_hash", "created_at",
    }  # fmt: skip
    assert set(schemas["ReplayCheck"]["properties"]) == {"compatible", "drift"}
    assert set(schemas["InputDrift"]["properties"]) == {
        "input", "expected_columns", "found_columns", "suggestions",
    }  # fmt: skip
    assert set(schemas["ColumnSuggestion"]["properties"]) == {"expected", "found"}
