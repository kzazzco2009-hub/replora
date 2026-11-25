"""P0.5: the §5 registry contract (operations and limits) is served as 501 stubs."""

import pytest

ENDPOINTS = [("/api/v1/operations", "operations_list"), ("/api/v1/limits", "limits_get")]
ARTIFACT_TYPES = {
    "RawFile",
    "ArchiveManifest",
    "TabularArtifact",
    "TextDocumentArtifact",
    "PagedArtifact",
    "PresentationArtifact",
    "ImageArtifact",
    "StructuredObjectArtifact",
    "ValidationReport",
    "ComparisonReport",
    "OutputFile",
}


def responses(openapi: dict, path: str) -> dict:
    return openapi["paths"][path]["get"]["responses"]


@pytest.mark.parametrize(("path", "operation_id"), ENDPOINTS)
def test_stub_answers_501_problem_json(client, path, operation_id):
    response = client.get(path)

    assert response.status_code == 501
    assert response.json()["code"] == "NOT_IMPLEMENTED"


@pytest.mark.parametrize(("path", "operation_id"), ENDPOINTS)
def test_registry_is_public_and_cached_for_an_hour(openapi, path, operation_id):
    documented = responses(openapi, path)

    assert documented["200"]["headers"]["Cache-Control"]["schema"]["example"] == (
        "public, max-age=3600"
    )
    assert not {"401", "403", "404"} & set(documented)


@pytest.mark.parametrize(("path", "operation_id"), ENDPOINTS)
def test_operation_ids(openapi, path, operation_id):
    assert openapi["paths"][path]["get"]["operationId"] == operation_id


def test_operations_returns_a_list_of_operation_contracts(openapi):
    schema = responses(openapi, "/api/v1/operations")["200"]["content"]["application/json"]

    assert schema["schema"]["items"] == {"$ref": "#/components/schemas/OperationContract"}


def test_operation_contract_matches_contract(schemas):
    contract = schemas["OperationContract"]

    assert set(contract["properties"]) == {
        "id", "version", "title_key", "inputs", "outputs", "params_schema",
    }  # fmt: skip
    assert set(contract["required"]) == set(contract["properties"])
    assert contract["properties"]["params_schema"]["type"] == "object"


def test_port_artifact_type_is_one_of_the_11_kinds(schemas):
    port = schemas["Port"]

    assert set(port["properties"]) == {"name", "artifact_type", "required"}
    assert set(schemas["ArtifactType"]["enum"]) == ARTIFACT_TYPES


def test_limits_are_integers_in_bytes_and_counts(schemas):
    limits = schemas["Limits"]["properties"]

    assert set(limits) == {"max_file_size", "max_files_per_run", "max_nodes", "workspace_quota"}
    assert {field["type"] for field in limits.values()} == {"integer"}
