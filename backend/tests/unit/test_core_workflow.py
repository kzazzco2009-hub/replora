"""P1.2 workflow definitions: nodes, edges, IO contracts and policies are frozen and strict."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.artifact_type import ArtifactType
from app.core.operations import OperationRef
from app.core.workflow import (
    Edge,
    InputContract,
    Node,
    OutputContract,
    PortRef,
    ResourcePolicy,
    ReviewPolicy,
    WorkflowDefinition,
)


def _definition(**overrides) -> WorkflowDefinition:
    fields = {
        "nodes": [
            Node(
                id="parse",
                operation=OperationRef(id="parse_csv", version=1),
                params={"delimiter": ",", "header": True},
                label="قراءة الملف",
            ),
            Node(id="normalize", operation=OperationRef(id="normalize_columns", version=1)),
        ],
        "edges": [
            Edge(
                source=PortRef(node_id="parse", port="table"),
                target=PortRef(node_id="normalize", port="table"),
            )
        ],
        "inputs": [
            InputContract(
                name="orders",
                artifact_type=ArtifactType.RAW_FILE,
                columns=["order_id", "amount"],
                targets=[PortRef(node_id="parse", port="file")],
            )
        ],
        "outputs": [
            OutputContract(
                name="clean",
                artifact_type=ArtifactType.TABULAR,
                source=PortRef(node_id="normalize", port="table"),
            )
        ],
    }
    return WorkflowDefinition(**{**fields, **overrides})


def _saved() -> WorkflowDefinition:
    return _definition(workflow_id=uuid4(), workflow_version=3)


def test_a_draft_has_no_workflow_id_and_schema_version_1():
    definition = _definition()
    assert definition.workflow_id is None
    assert definition.workflow_version is None
    assert definition.schema_version == 1


def test_default_policies_follow_the_documented_limits():
    policy = _definition().resource_policy
    assert policy == ResourcePolicy()
    assert (policy.max_files, policy.max_file_size) == (10, 50 * 1024 * 1024)
    assert (policy.node_timeout_seconds, policy.run_timeout_seconds) == (120, 900)
    assert _definition().review_policy == ReviewPolicy(on_warning="review")


@pytest.mark.parametrize("make", [_definition, _saved])
def test_round_trip_is_identical(make):
    definition = make()
    assert WorkflowDefinition.model_validate(definition.model_dump()) == definition
    assert WorkflowDefinition.model_validate_json(definition.model_dump_json()) == definition


@pytest.mark.parametrize(
    "path",
    [
        (),
        ("nodes", 0),
        ("edges", 0),
        ("edges", 0, "source"),
        ("inputs", 0),
        ("outputs", 0),
        ("resource_policy",),
        ("review_policy",),
    ],
)
def test_extra_fields_are_rejected_everywhere(path):
    data = _definition().model_dump(mode="json")
    target = data
    for key in path:
        target = target[key]
    target["surprise"] = 1
    with pytest.raises(ValidationError, match="extra_forbidden"):
        WorkflowDefinition.model_validate(data)


def test_definition_is_frozen():
    definition = _definition()
    with pytest.raises(ValidationError, match="frozen_instance"):
        definition.nodes = []
    with pytest.raises(ValidationError, match="frozen_instance"):
        definition.nodes[0].params = {}


def test_an_empty_workflow_is_a_valid_shape():
    """Emptiness and dangling references are the validator's job (P2.2), not the model's."""
    assert _definition(nodes=[], edges=[], inputs=[], outputs=[]).nodes == []


@pytest.mark.parametrize("bad", ["", "has space", "x" * 65, "ü"])
def test_node_ids_and_port_names_are_short_ascii_names(bad):
    with pytest.raises(ValidationError):
        Node(id=bad, operation=OperationRef(id="parse_csv", version=1))
    with pytest.raises(ValidationError):
        PortRef(node_id="parse", port=bad)


@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": 2},
        {"workflow_version": 0},
        {"workflow_id": uuid4()},
        {"workflow_version": 1},
    ],
)
def test_versions_are_checked(overrides):
    with pytest.raises(ValidationError):
        _definition(**overrides)


@pytest.mark.parametrize(
    "policy",
    [
        {"max_files": 11},
        {"max_files": 0},
        {"node_timeout_seconds": 121},
        {"run_timeout_seconds": 901},
        {"max_file_size": 0},
    ],
)
def test_resource_policy_stays_within_the_platform_limits(policy):
    with pytest.raises(ValidationError):
        ResourcePolicy(**policy)


def test_params_must_be_json_values():
    with pytest.raises(ValidationError):
        Node(id="n", operation=OperationRef(id="op", version=1), params={"when": object()})


def test_unknown_review_policy_is_rejected():
    with pytest.raises(ValidationError):
        ReviewPolicy(on_warning="ignore")


def test_inputs_and_outputs_take_an_optional_unicode_label():
    """A display name for an upload slot or a result (frontend note on #56)."""
    definition = _definition(
        inputs=[
            InputContract(
                name="orders",
                label="الطلبات",
                artifact_type=ArtifactType.RAW_FILE,
                targets=[PortRef(node_id="parse", port="file")],
            )
        ],
        outputs=[
            OutputContract(
                name="clean",
                label="النتيجة",
                artifact_type=ArtifactType.TABULAR,
                source=PortRef(node_id="normalize", port="table"),
            )
        ],
    )
    assert definition.inputs[0].label == "الطلبات"
    assert definition.outputs[0].label == "النتيجة"
    assert _definition().inputs[0].label is None
    assert WorkflowDefinition.model_validate_json(definition.model_dump_json()) == definition


@pytest.mark.parametrize("model", [InputContract, OutputContract])
def test_io_labels_are_at_most_100_characters(model):
    port = PortRef(node_id="n", port="p")
    fields = {"targets": [port]} if model is InputContract else {"source": port}
    with pytest.raises(ValidationError, match="at most 100 characters"):
        model(name="x", label="x" * 101, artifact_type=ArtifactType.TABULAR, **fields)
