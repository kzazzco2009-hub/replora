"""P0.5: the §6 templates and drafts contract is served as 501 stubs and documented in OpenAPI."""

import pytest

UUID = "01937a5e-7f00-7000-8000-000000000001"
IDS = {"ws_id": UUID, "draft_id": UUID}
TEMPLATES = "/api/v1/templates"
DRAFTS = "/api/v1/workspaces/{ws_id}/drafts"
DRAFT = f"{DRAFTS}/{{draft_id}}"
PROBLEM = {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}}
CREATE = {"file_ids": [UUID], "prompt": "", "planner": "template", "template_id": "reconcile"}
UPDATE = {"definition": {"nodes": [], "edges": [], "inputs": [], "outputs": []}}

# (method, OpenAPI path, success status, sample valid body) — docs/api_contract.md §6.
ENDPOINTS = [
    ("get", TEMPLATES, 200, None),
    ("post", DRAFTS, 201, CREATE),
    ("get", DRAFT, 200, None),
    ("patch", DRAFT, 200, UPDATE),
]
DRAFT_ENDPOINTS = ENDPOINTS[1:]


def operation(openapi: dict, method: str, path: str) -> dict:
    return openapi["paths"][path][method]


@pytest.mark.parametrize(("method", "path", "status", "body"), ENDPOINTS)
def test_endpoint_is_documented_with_its_success_status(openapi, method, path, status, body):
    assert str(status) in operation(openapi, method, path)["responses"]


@pytest.mark.parametrize(("method", "path", "status", "body"), ENDPOINTS)
def test_stub_answers_501_problem_json(client, method, path, status, body):
    response = client.request(method, path.format(**IDS), json=body, headers={"If-Match": '"1"'})

    assert response.status_code == 501
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "NOT_IMPLEMENTED"


def test_all_contract_paths_and_nothing_else(openapi):
    documented = {
        (method, path)
        for path, operations in openapi["paths"].items()
        if path.startswith((TEMPLATES, DRAFTS))
        for method in operations
    }

    assert documented == {(method, path) for method, path, _, _ in ENDPOINTS}


def test_operation_ids_name_the_resource(openapi):
    ids = [operation(openapi, method, path)["operationId"] for method, path, _, _ in ENDPOINTS]

    assert ids == ["templates_list", "drafts_create", "drafts_get", "drafts_update"]


def test_templates_are_public_and_cached_for_an_hour(openapi):
    responses = operation(openapi, "get", TEMPLATES)["responses"]

    assert responses["200"]["headers"]["Cache-Control"]["schema"]["example"] == (
        "public, max-age=3600"
    )
    assert not {"401", "403", "404"} & set(responses)


@pytest.mark.parametrize(("method", "path", "status", "body"), DRAFT_ENDPOINTS)
def test_draft_responses_carry_an_etag(openapi, method, path, status, body):
    success = operation(openapi, method, path)["responses"][str(status)]

    assert "ETag" in success["headers"]
    assert success["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/Draft"
    }


@pytest.mark.parametrize(("method", "path", "status", "body"), DRAFT_ENDPOINTS)
def test_draft_errors_include_404(openapi, method, path, status, body):
    responses = operation(openapi, method, path)["responses"]

    for error in ("401", "403", "404", "422", "429", "501"):
        assert responses[error]["content"] == PROBLEM


def test_only_patch_documents_the_preconditions(openapi):
    with_412 = {
        (method, path)
        for method, path, _, _ in ENDPOINTS
        if {"412", "428"} & set(operation(openapi, method, path)["responses"])
    }
    patch = operation(openapi, "patch", DRAFT)

    assert with_412 == {("patch", DRAFT)}
    assert patch["responses"]["412"]["content"] == PROBLEM
    assert patch["responses"]["428"]["content"] == PROBLEM
    assert ("header", "If-Match") in {(param["in"], param["name"]) for param in patch["parameters"]}


CREATE_ERRORS = [
    ({"file_ids": []}, "body.file_ids", "TOO_SHORT"),
    ({"file_ids": [UUID] * 11}, "body.file_ids", "TOO_LONG"),
    ({"prompt": "x" * 4001}, "body.prompt", "STRING_TOO_LONG"),
    ({"planner": "mock"}, "body.planner", "LITERAL_ERROR"),
]


@pytest.mark.parametrize(("change", "path", "code"), CREATE_ERRORS)
def test_create_body_limits(client, change, path, code):
    response = client.post(DRAFTS.format(**IDS), json=CREATE | change)

    assert response.status_code == 422
    assert [(error["path"], error["code"]) for error in response.json()["errors"]] == [(path, code)]


def test_create_body_matches_contract(schemas):
    body = schemas["DraftCreate"]["properties"]

    assert set(body) == {"file_ids", "prompt", "planner", "template_id", "share_samples"}
    assert body["planner"]["enum"] == ["template", "ai"]
    assert body["share_samples"]["default"] is False


def test_draft_schema_matches_contract(schemas):
    assert set(schemas["Draft"]["properties"]) == {
        "id", "prompt", "planner", "definition", "plan_hash", "explanation", "ai_disclosure",
        "validation", "created_at",
    }  # fmt: skip
    assert set(schemas["Explanation"]["properties"]) == {"key", "params", "text"}
    assert set(schemas["AiDisclosure"]["properties"]) == {"sent_fields", "samples_sent"}
    assert set(schemas["ValidationReport"]["properties"]) == {"valid", "errors", "warnings"}
    assert set(schemas["Issue"]["properties"]) == {"code", "path", "node_id", "params"}
    assert set(schemas["WorkflowDefinition"]["properties"]) == {
        "workflow_id", "workflow_version", "schema_version", "nodes", "edges", "inputs", "outputs",
        "resource_policy", "review_policy",
    }  # fmt: skip
    assert schemas["WorkflowDefinition"]["additionalProperties"] is False


def test_a_draft_update_must_be_a_typed_definition(client):
    url = DRAFT.format(**IDS)
    headers = {"If-Match": '"1"'}

    for definition in ({}, {"nodes": [], "edges": []}, UPDATE["definition"] | {"code": "x"}):
        response = client.patch(url, json={"definition": definition}, headers=headers)
        assert response.status_code == 422


def test_template_schema_matches_contract(schemas):
    template = schemas["Template"]["properties"]

    assert set(template) == {"id", "title_key", "description_key", "required_inputs"}
    assert set(schemas["TemplateInput"]["properties"]) == {"title_key", "artifact_type"}
