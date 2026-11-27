"""P2.1 operation registry: register and look up by `(id, version)`, duplicates rejected (T2.1)."""

import pytest

from app.core.artifact_type import ArtifactType
from app.core.operations import OperationContract, Port
from app.core.registry import OperationRegistry, RegistryError


def contract(op_id: str = "parse_csv", version: int = 1, params_schema=None) -> OperationContract:
    return OperationContract(
        id=op_id,
        version=version,
        title_key=f"operations.{op_id}.title",
        inputs=[Port(name="file", artifact_type=ArtifactType.RAW_FILE, required=True)],
        outputs=[Port(name="table", artifact_type=ArtifactType.TABULAR, required=True)],
        params_schema=params_schema if params_schema is not None else {"type": "object"},
    )


def test_register_and_get():
    registry = OperationRegistry()
    parse = contract()
    registry.register(parse)
    assert registry.get("parse_csv", 1) is parse


def test_two_versions_of_one_operation_live_side_by_side():
    registry = OperationRegistry([contract(version=1), contract(version=2)])
    assert registry.get("parse_csv", 2).version == 2
    assert registry.versions("parse_csv") == [1, 2]


def test_a_duplicate_id_and_version_is_rejected():
    registry = OperationRegistry([contract()])
    with pytest.raises(RegistryError) as caught:
        registry.register(contract())
    assert caught.value.code == "OP_DUPLICATE"


def test_an_unknown_operation_is_op_unknown():
    with pytest.raises(RegistryError) as caught:
        OperationRegistry().get("nope", 1)
    assert caught.value.code == "OP_UNKNOWN"
    assert caught.value.params == {"operation": "nope", "version": 1}


def test_an_unknown_version_of_a_known_operation_is_op_version_invalid():
    with pytest.raises(RegistryError) as caught:
        OperationRegistry([contract()]).get("parse_csv", 2)
    assert caught.value.code == "OP_VERSION_INVALID"
    assert caught.value.params == {"operation": "parse_csv", "version": 2, "known": [1]}


def test_list_is_sorted_by_id_then_version():
    registry = OperationRegistry([contract("reconcile"), contract(version=2), contract()])
    assert [(op.id, op.version) for op in registry.list()] == [
        ("parse_csv", 1),
        ("parse_csv", 2),
        ("reconcile", 1),
    ]


@pytest.mark.parametrize("version", [0, -1])
def test_a_version_below_one_cannot_be_registered(version):
    with pytest.raises(RegistryError) as caught:
        OperationRegistry([contract(version=version)])
    assert caught.value.code == "OP_VERSION_INVALID"


@pytest.mark.parametrize(
    "params_schema",
    [
        {"type": "object", "properties": {"x": {"oneOf": [{"type": "string"}]}}},
        {"type": "object", "properties": {"x": {"anyOf": [{"type": "string"}]}}},
        {"type": "object", "properties": {"x": {"$ref": "#/$defs/y"}}},
        {"type": "object", "properties": {"x": {"type": "number"}}},
        {"type": "object", "properties": {"x": {"type": "array", "items": {"type": "integer"}}}},
        {"type": "string"},
        {"type": "object", "properties": {"x": {"type": "strng"}}},
    ],
)
def test_a_params_schema_outside_the_contract_subset_is_rejected(params_schema):
    with pytest.raises(RegistryError) as caught:
        OperationRegistry([contract(params_schema=params_schema)])
    assert caught.value.code == "OP_PARAMS_SCHEMA_INVALID"


def test_the_supported_subset_is_accepted():
    schema = {
        "type": "object",
        "required": ["key"],
        "additionalProperties": False,
        "properties": {
            "key": {"type": "string", "x-replora-widget": "column"},
            "tolerance": {"type": "string", "pattern": "^[0-9]+(\\.[0-9]+)?$"},
            "limit": {"type": "integer", "minimum": 1},
            "strict": {"type": "boolean", "default": False},
            "mode": {"type": "string", "enum": ["exact", "fuzzy"]},
            "columns": {"type": "array", "items": {"type": "string"}},
        },
    }
    registry = OperationRegistry([contract(params_schema=schema)])
    assert registry.get("parse_csv", 1).params_schema == schema
