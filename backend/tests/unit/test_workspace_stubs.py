"""P0.5: the §3 workspaces contract is served as 501 stubs and documented in OpenAPI."""

import pytest

UUID = "01937a5e-7f00-7000-8000-000000000001"
IDS = {"ws_id": UUID, "invitation_id": UUID, "user_id": UUID}
WS = "/api/v1/workspaces/{ws_id}"
PROBLEM = {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}}

# (method, OpenAPI path, success status, sample valid body) — docs/api_contract.md §3.
ENDPOINTS = [
    ("get", "/api/v1/workspaces", 200, None),
    ("post", "/api/v1/workspaces", 201, {"name": "Finance"}),
    ("delete", WS, 204, None),
    ("get", f"{WS}/members", 200, None),
    ("patch", f"{WS}/members/{{user_id}}", 200, {"role": "viewer"}),
    ("delete", f"{WS}/members/{{user_id}}", 204, None),
    ("post", f"{WS}/invitations", 201, {"email": "b@example.com", "role": "member"}),
    ("get", f"{WS}/invitations", 200, None),
    ("delete", f"{WS}/invitations/{{invitation_id}}", 204, None),
    ("post", "/api/v1/invitations/accept", 200, {"token": "t"}),
    ("get", f"{WS}/audit", 200, None),
]
SCOPED = [endpoint for endpoint in ENDPOINTS if endpoint[1].startswith(WS)]
UNSCOPED = [endpoint for endpoint in ENDPOINTS if not endpoint[1].startswith(WS)]


def responses(openapi: dict, method: str, path: str) -> dict:
    return openapi["paths"][path][method]["responses"]


@pytest.mark.parametrize(("method", "path", "status", "body"), ENDPOINTS)
def test_endpoint_is_documented_with_its_success_status(openapi, method, path, status, body):
    assert str(status) in responses(openapi, method, path)


REAL = {("get", "/api/v1/workspaces"), ("post", "/api/v1/workspaces"), ("delete", WS),
        ("get", f"{WS}/members"), ("patch", f"{WS}/members/{{user_id}}"),
        ("delete", f"{WS}/members/{{user_id}}")}  # fmt: skip
"""Implemented in P5.8; their behaviour is tested in tests/integration/test_workspaces_api.py."""
STUBS = [e for e in ENDPOINTS if (e[0], e[1]) not in REAL]


@pytest.mark.parametrize(("method", "path", "status", "body"), STUBS)
def test_stub_answers_501_problem_json(client, method, path, status, body):
    response = client.request(method, path.format(**IDS), json=body)

    assert response.status_code == 501
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "NOT_IMPLEMENTED"


def test_all_contract_paths_and_nothing_else(openapi):
    documented = {
        (method, path)
        for path, operations in openapi["paths"].items()
        if path.startswith(("/api/v1/workspaces", "/api/v1/invitations"))
        and not any(section in path for section in ("/files", "/drafts", "/runs", "/workflows"))
        for method in operations
    }

    assert documented == {(method, path) for method, path, _, _ in ENDPOINTS}


@pytest.mark.parametrize(("method", "path", "status", "body"), SCOPED)
def test_workspace_scoped_errors_include_404(openapi, method, path, status, body):
    for error in ("401", "403", "404", "409", "422", "429", "501"):
        assert responses(openapi, method, path)[error]["content"] == PROBLEM


@pytest.mark.parametrize(("method", "path", "status", "body"), UNSCOPED)
def test_unscoped_routes_document_no_404(openapi, method, path, status, body):
    assert "404" not in responses(openapi, method, path)


@pytest.mark.parametrize("path", [f"{WS}/invitations", f"{WS}/members/{{user_id}}"])
def test_owner_role_cannot_be_granted(client, path):
    invite = path.endswith("invitations")
    body = {"role": "owner"} | ({"email": "b@example.com"} if invite else {})

    response = client.request("post" if invite else "patch", path.format(**IDS), json=body)

    assert response.status_code == 422


def test_path_ids_must_be_uuids(client):
    assert client.get("/api/v1/workspaces/not-a-uuid/members").status_code == 422


def test_audit_is_a_cursor_page_with_limit_up_to_100(client, openapi, schemas):
    operation = openapi["paths"][f"{WS}/audit"]["get"]
    page = operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]

    assert set(schemas[page.rsplit("/", 1)[1]]["properties"]) == {"items", "next_cursor"}
    assert {"cursor", "limit"} <= {parameter["name"] for parameter in operation["parameters"]}
    assert client.get(f"{WS}/audit".format(**IDS), params={"limit": 101}).status_code == 422


def test_member_and_invitation_schemas_match_contract(schemas):
    assert set(schemas["Member"]["properties"]) == {"user_id", "email", "display_name", "role"}
    invitation = schemas["Invitation"]["properties"]
    assert set(invitation) == {"id", "email", "role", "invited_by", "expires_at", "status"}
    assert invitation["status"]["enum"] == ["pending", "accepted", "revoked", "expired"]


def test_audit_event_schema_matches_contract(schemas):
    assert set(schemas["AuditEvent"]["properties"]) == {
        "id", "actor_id", "action", "target_type", "target_id", "created_at",
    }  # fmt: skip


def test_operation_ids_name_the_resource(openapi):
    ids = {op["operationId"] for ops in openapi["paths"].values() for op in ops.values()}

    assert {"workspaces_list", "workspaces_delete", "workspaces_accept_invitation"} <= ids


@pytest.mark.parametrize("email", ["x", 5])
def test_invitation_email_error_is_invalid_email(client, email):
    path = f"{WS}/invitations".format(**IDS)
    response = client.post(path, json={"email": email, "role": "member"})

    assert response.status_code == 422
    expected = [{"path": "body.email", "code": "INVALID_EMAIL", "params": {}}]
    assert response.json()["errors"] == expected


AUDIT_ACTIONS = {
    "workspace.created",
    "member.invited",
    "member.invitation_revoked",
    "member.joined",
    "member.role_changed",
    "member.removed",
    "file.uploaded",
    "file.downloaded",
    "file.deleted",
    "workflow.saved",
    "workflow.deleted",
    "run.created",
    "run.approved",
    "run.cancelled",
    "output.downloaded",
    "planner.called",
}
AUDIT_TARGETS = {"workspace", "invitation", "member", "file", "workflow", "draft", "run", "output"}


def test_audit_action_and_target_type_are_fixed_lists(schemas):
    properties = schemas["AuditEvent"]["properties"]

    assert set(properties["action"]["enum"]) == AUDIT_ACTIONS
    assert set(properties["target_type"]["enum"]) == AUDIT_TARGETS


def test_every_audit_action_names_a_target_type():
    assert {action.split(".")[0] for action in AUDIT_ACTIONS} - {"planner"} <= AUDIT_TARGETS
