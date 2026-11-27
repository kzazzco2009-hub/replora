"""§5 registry: `GET /operations` and `GET /limits` serve the real registry and server limits,
publicly and cached for an hour (P8.1, P8.5)."""

import pytest

from app.core.limits import MAX_DEPTH, MAX_FAN_IN, MAX_FAN_OUT, MAX_NODES
from app.files.service import MAX_FILE_SIZE, MAX_FILES_PER_RUN
from app.ops.registry import REGISTRY

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
def test_served_without_a_session_and_cached_publicly(client, path, operation_id):
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["cache-control"] == "public, max-age=3600"


def test_operations_lists_every_registered_contract(client):
    body = client.get("/api/v1/operations").json()

    assert [(op["id"], op["version"]) for op in body] == [
        (op.id, op.version) for op in REGISTRY.list()
    ]
    assert body[0] == REGISTRY.list()[0].model_dump(mode="json")


def test_limits_are_the_ones_the_server_enforces(client):
    assert client.get("/api/v1/limits").json() == {
        "max_file_size": MAX_FILE_SIZE, "max_files_per_run": MAX_FILES_PER_RUN,
        "max_nodes": MAX_NODES, "max_depth": MAX_DEPTH, "max_fan_in": MAX_FAN_IN,
        "max_fan_out": MAX_FAN_OUT,
        "workspace_quota": client.app.state.settings.workspace_quota_bytes,
    }  # fmt: skip


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

    assert set(limits) == {
        "max_file_size", "max_files_per_run", "max_nodes", "max_depth", "max_fan_in",
        "max_fan_out", "workspace_quota",
    }  # fmt: skip
    assert {field["type"] for field in limits.values()} == {"integer"}
