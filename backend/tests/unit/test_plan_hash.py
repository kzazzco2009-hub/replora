"""P1.4 plan_hash: one stable SHA-256 per meaning, a new one for any change (T1.3, T1.4, S-11)."""

import json
import math
from random import Random

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from app.core.artifact_type import ArtifactType
from app.core.operations import OperationRef
from app.core.plan_hash import canonical_json, plan_hash
from app.core.workflow import Edge, InputContract, Node, OutputContract, PortRef, WorkflowDefinition

MAX_SAFE = 2**53 - 1
names = st.from_regex(r"[A-Za-z0-9_-]{1,8}", fullmatch=True)
scalars = (
    st.none()
    | st.booleans()
    | st.integers(-MAX_SAFE, MAX_SAFE)
    | st.floats(allow_nan=False, allow_infinity=False)
    | st.text(max_size=8)
)
json_values = st.recursive(
    scalars,
    lambda inner: (
        st.lists(inner, max_size=3) | st.dictionaries(st.text(max_size=5), inner, max_size=3)
    ),
    max_leaves=8,
)
ports = st.builds(PortRef, node_id=names, port=names)
nodes = st.builds(
    Node,
    id=names,
    operation=st.builds(OperationRef, id=names, version=st.integers(1, 9)),
    params=st.dictionaries(names, json_values, max_size=3),
    label=st.none() | st.text(max_size=10),
)
definitions = st.builds(
    WorkflowDefinition,
    nodes=st.lists(nodes, min_size=1, max_size=4),
    edges=st.lists(st.builds(Edge, source=ports, target=ports), max_size=3),
    inputs=st.lists(
        st.builds(
            InputContract,
            name=names,
            artifact_type=st.sampled_from(ArtifactType),
            columns=st.lists(st.text(max_size=6), max_size=3),
            targets=st.lists(ports, max_size=2),
        ),
        max_size=2,
    ),
    outputs=st.lists(
        st.builds(
            OutputContract, name=names, artifact_type=st.sampled_from(ArtifactType), source=ports
        ),
        max_size=2,
    ),
)


def _shuffled(value, rng: Random):
    """The same JSON value with every object's keys in a random order."""
    if isinstance(value, dict):
        keys = list(value)
        rng.shuffle(keys)
        return {key: _shuffled(value[key], rng) for key in keys}
    if isinstance(value, list):
        return [_shuffled(item, rng) for item in value]
    return value


def _changed(definition: WorkflowDefinition, **updates) -> WorkflowDefinition:
    return WorkflowDefinition.model_validate({**definition.model_dump(mode="json"), **updates})


GOLDEN = WorkflowDefinition(
    nodes=[
        Node(
            id="parse",
            operation=OperationRef(id="parse_csv", version=1),
            params={"delimiter": ",", "skip": 2.0, "header": True},
            label="قراءة",
        )
    ],
    edges=[],
    inputs=[],
    outputs=[],
)


def test_golden_hash_is_stable_across_runs_and_machines():
    assert plan_hash(GOLDEN) == "0edcdef65b0bcf15dc468d63fc62d578b56a9745c6bfdda378afa475a87008e0"


def test_hash_is_64_lowercase_hex():
    digest = plan_hash(GOLDEN)
    assert len(digest) == 64
    assert digest == digest.lower()
    int(digest, 16)


def test_canonical_form_is_sorted_compact_utf8():
    text = canonical_json({"b": [1, {"d": 1, "c": "قراءة"}], "a": None}).decode("utf-8")
    assert text == '{"a":null,"b":[1,{"c":"قراءة","d":1}]}'


@pytest.mark.parametrize(("left", "right"), [(2.0, 2), (-0.0, 0), (1e15, 10**15)])
def test_numbers_that_json_cannot_tell_apart_hash_the_same(left, right):
    assert canonical_json({"x": left}) == canonical_json({"x": right})


def test_non_integral_and_huge_floats_keep_their_value():
    assert canonical_json({"x": 0.1}) == b'{"x":0.1}'
    assert canonical_json({"x": 1e300}) == b'{"x":1e+300}'


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_nan_and_infinity_are_rejected(bad):
    with pytest.raises(ValueError):
        canonical_json({"x": bad})


@given(definition=definitions, rng=st.randoms())
def test_key_order_and_whitespace_never_change_the_hash(definition, rng):
    """T1.3."""
    data = _shuffled(definition.model_dump(mode="json"), rng)
    reordered = WorkflowDefinition.model_validate_json(json.dumps(data, indent=3))
    assert reordered == definition
    assert plan_hash(reordered) == plan_hash(definition)


@given(definition=definitions, value=json_values)
def test_adding_a_node_param_changes_the_hash(definition, value):
    """T1.4: params. `~` can't appear in a generated key, so the key is always new."""
    data = definition.model_dump(mode="json")
    data["nodes"][0]["params"]["~new"] = value
    assert plan_hash(WorkflowDefinition.model_validate(data)) != plan_hash(definition)


@given(definition=definitions, value=json_values)
def test_changing_a_node_param_value_changes_the_hash(definition, value):
    """T1.4: params."""
    params = definition.nodes[0].params
    assume(params)
    key = next(iter(params))
    assume(canonical_json(value) != canonical_json(params[key]))
    data = definition.model_dump(mode="json")
    data["nodes"][0]["params"][key] = value
    assert plan_hash(WorkflowDefinition.model_validate(data)) != plan_hash(definition)


@given(definition=definitions, edge=st.builds(Edge, source=ports, target=ports))
def test_an_edge_change_changes_the_hash(definition, edge):
    """T1.4: edges."""
    edges = [*definition.model_dump(mode="json")["edges"], edge.model_dump(mode="json")]
    assert plan_hash(_changed(definition, edges=edges)) != plan_hash(definition)


@given(definition=definitions)
def test_an_operation_or_workflow_version_change_changes_the_hash(definition):
    """T1.4: versions."""
    data = definition.model_dump(mode="json")
    data["nodes"][0]["operation"]["version"] += 1
    assert plan_hash(WorkflowDefinition.model_validate(data)) != plan_hash(definition)
    v1 = _changed(
        definition, workflow_id="01937a5e-7f00-7000-8000-000000000001", workflow_version=1
    )
    v2 = _changed(
        definition, workflow_id="01937a5e-7f00-7000-8000-000000000001", workflow_version=2
    )
    assert plan_hash(v1) != plan_hash(v2)
