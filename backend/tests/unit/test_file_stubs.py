"""P0.5: the §4 files contract is served as 501 stubs and documented in OpenAPI."""

import pytest

UUID = "01937a5e-7f00-7000-8000-000000000001"
IDS = {"ws_id": UUID, "file_id": UUID}
FILES = "/api/v1/workspaces/{ws_id}/files"
PROBLEM = {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}}
INTENT = {"display_name": "orders.csv", "size": 1024, "content_type": "text/csv"}

# (method, OpenAPI path, success status, sample valid body) — docs/api_contract.md §4.
ENDPOINTS = [
    ("post", f"{FILES}/upload-intent", 201, INTENT),
    ("post", f"{FILES}/{{file_id}}/complete", 200, None),
    ("post", f"{FILES}/samples", 201, None),
    ("get", FILES, 200, None),
    ("get", f"{FILES}/{{file_id}}", 200, None),
    ("get", f"{FILES}/{{file_id}}/download", 200, None),
    ("delete", f"{FILES}/{{file_id}}", 204, None),
]


def operation(openapi: dict, method: str, path: str) -> dict:
    return openapi["paths"][path][method]


@pytest.mark.parametrize(("method", "path", "status", "body"), ENDPOINTS)
def test_endpoint_is_documented_with_its_success_status(openapi, method, path, status, body):
    assert str(status) in operation(openapi, method, path)["responses"]


@pytest.mark.parametrize(("method", "path", "status", "body"), ENDPOINTS)
def test_stub_answers_501_problem_json(client, method, path, status, body):
    response = client.request(method, path.format(**IDS), json=body)

    assert response.status_code == 501
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "NOT_IMPLEMENTED"


def test_all_contract_paths_and_nothing_else(openapi):
    documented = {
        (method, path)
        for path, operations in openapi["paths"].items()
        if path.startswith(FILES)
        for method in operations
    }

    assert documented == {(method, path) for method, path, _, _ in ENDPOINTS}


@pytest.mark.parametrize(("method", "path", "status", "body"), ENDPOINTS)
def test_errors_include_404(openapi, method, path, status, body):
    responses = operation(openapi, method, path)["responses"]

    for error in ("401", "403", "404", "409", "422", "429", "501"):
        assert responses[error]["content"] == PROBLEM


def test_only_upload_intent_documents_413(openapi):
    with_413 = {
        path
        for method, path, _, _ in ENDPOINTS
        if "413" in operation(openapi, method, path)["responses"]
    }

    assert with_413 == {f"{FILES}/upload-intent"}
    assert (
        operation(openapi, "post", f"{FILES}/upload-intent")["responses"]["413"]["content"]
        == PROBLEM
    )


@pytest.mark.parametrize("change", [{"sha256": "00"}, {"size": 0}])
def test_upload_intent_rejects_client_hash_and_empty_file(client, change):
    response = client.post(f"{FILES}/upload-intent".format(**IDS), json=INTENT | change)

    assert response.status_code == 422


def test_path_ids_must_be_uuids(client):
    assert client.get(f"{FILES}/not-a-uuid".format(ws_id=UUID)).status_code == 422


def test_list_is_a_cursor_page_filtered_by_detected_type(client, openapi, schemas):
    listing = operation(openapi, "get", FILES)
    page = listing["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]

    assert set(schemas[page.rsplit("/", 1)[1]]["properties"]) == {"items", "next_cursor"}
    assert {"cursor", "limit", "type"} <= {parameter["name"] for parameter in listing["parameters"]}
    assert client.get(FILES.format(**IDS), params={"limit": 101}).status_code == 422
    assert client.get(FILES.format(**IDS), params={"type": "exe"}).status_code == 422


def test_file_schema_matches_contract(schemas):
    file = schemas["File"]["properties"]

    assert set(file) == {
        "id", "display_name", "detected_type", "size", "sha256", "status", "rejection_code",
        "members", "uploaded_by", "created_at", "expires_at",
    }  # fmt: skip
    assert file["status"]["enum"] == ["pending", "ready", "rejected"]
    assert set(schemas["FileMember"]["properties"]) == {"path", "detected_type", "size"}


def test_upload_intent_response_matches_contract(schemas):
    upload = schemas["UploadTarget"]["properties"]

    assert set(schemas["UploadIntent"]["properties"]) == {"file_id", "upload"}
    assert set(upload) == {"url", "method", "headers", "expires_at"}
    assert upload["method"]["const"] == "PUT"


def test_operation_ids_name_the_resource(openapi):
    ids = {op["operationId"] for ops in openapi["paths"].values() for op in ops.values()}

    assert {"files_create_upload_intent", "files_list", "files_get", "files_delete"} <= ids
