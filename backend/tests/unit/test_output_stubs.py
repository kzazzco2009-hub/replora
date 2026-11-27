"""P0.5: the §7 run outputs are documented. List and download are real (P8.1,
`tests/integration/test_outputs_api.py`); preview and lineage are still 501."""

import pytest

UUID = "01937a5e-7f00-7000-8000-000000000001"
IDS = {"ws_id": UUID, "run_id": UUID, "artifact_id": UUID, "row": 0}
OUTPUTS = "/api/v1/workspaces/{ws_id}/runs/{run_id}/outputs"
ARTIFACT = f"{OUTPUTS}/{{artifact_id}}"
PROBLEM = {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}}

# (OpenAPI path, operationId) — docs/api_contract.md §7. All are GET with a 200.
ENDPOINTS = [
    (OUTPUTS, "outputs_list"),
    (f"{ARTIFACT}/preview", "outputs_preview"),
    (f"{ARTIFACT}/download", "outputs_download"),
    (f"{ARTIFACT}/rows/{{row}}/lineage", "outputs_lineage"),
]


def operation(openapi: dict, path: str) -> dict:
    return openapi["paths"][path]["get"]


@pytest.mark.parametrize(("path", "operation_id"), ENDPOINTS)
def test_endpoint_is_documented(openapi, path, operation_id):
    documented = operation(openapi, path)

    assert documented["operationId"] == operation_id
    assert "200" in documented["responses"]
    for error in ("401", "403", "404", "422", "429", "501"):
        assert documented["responses"][error]["content"] == PROBLEM


@pytest.mark.parametrize(("path", "operation_id"), [ENDPOINTS[1], ENDPOINTS[3]])
def test_preview_and_lineage_are_still_501_stubs(client, path, operation_id):
    response = client.get(path.format(**IDS))

    assert response.status_code == 501
    assert response.json()["code"] == "NOT_IMPLEMENTED"


def test_output_paths_are_all_documented(openapi):
    documented = {
        (method, path)
        for path, operations in openapi["paths"].items()
        if path.startswith(OUTPUTS)
        for method in operations
    }

    assert documented == {("get", path) for path, _ in ENDPOINTS}


PREVIEW_ERRORS = [
    ({"offset": -1}, "query.offset", "GREATER_THAN_EQUAL"),
    ({"limit": 0}, "query.limit", "GREATER_THAN_EQUAL"),
    ({"limit": 101}, "query.limit", "LESS_THAN_EQUAL"),
    ({"status": "other"}, "query.status", "LITERAL_ERROR"),
    ({"q": "x" * 201}, "query.q", "STRING_TOO_LONG"),
]


@pytest.mark.parametrize(("params", "path", "code"), PREVIEW_ERRORS)
def test_preview_query_limits(client, params, path, code):
    response = client.get(f"{ARTIFACT}/preview".format(**IDS), params=params)

    assert response.status_code == 422
    assert [(error["path"], error["code"]) for error in response.json()["errors"]] == [(path, code)]


def test_preview_filters_by_reconciliation_status(openapi, schemas):
    names = {param["name"] for param in operation(openapi, f"{ARTIFACT}/preview")["parameters"]}

    assert {"offset", "limit", "status", "q"} <= names
    assert set(schemas["Preview"]["properties"]) == {"columns", "rows", "total", "offset"}


def test_preview_row_carries_its_number_and_status(schemas):
    rows = schemas["Preview"]["properties"]["rows"]
    row = schemas["PreviewRow"]

    assert rows["items"] == {"$ref": "#/components/schemas/PreviewRow"}
    assert set(row["properties"]) == {"row", "status", "cells"}
    assert set(row["required"]) == {"row", "status", "cells"}
    assert row["properties"]["row"]["minimum"] == 0
    statuses = [option.get("enum") for option in row["properties"]["status"]["anyOf"]]
    assert statuses == [["matched", "value_diff", "missing_left", "missing_right"], None]


def test_integer_cells_stay_in_the_javascript_safe_range(schemas):
    cell_types = schemas["PreviewRow"]["properties"]["cells"]["items"]["anyOf"]
    integer = next(option for option in cell_types if option.get("type") == "integer")

    assert (integer["minimum"], integer["maximum"]) == (-(2**53 - 1), 2**53 - 1)


def test_lineage_row_is_a_non_negative_index(client):
    url = f"{ARTIFACT}/rows/-1/lineage".format(**IDS)

    assert client.get(url).status_code == 422


def test_output_schemas_match_contract(schemas):
    assert set(schemas["OutputArtifact"]["properties"]) == {
        "id", "name", "type", "format", "size", "row_count", "created_at",
    }  # fmt: skip
    assert set(schemas["Column"]["properties"]) == {"name", "type", "nullable"}
    assert schemas["Column"]["properties"]["type"]["enum"] == [
        "string", "decimal", "integer", "date", "boolean",
    ]  # fmt: skip
    assert set(schemas["Lineage"]["properties"]) == {"sources", "operations"}
    assert set(schemas["LineageSource"]["properties"]) == {"file_id", "member_path", "row", "page"}
    assert set(schemas["OperationRef"]["properties"]) == {"id", "version"}
