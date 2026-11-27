"""P2.3 type checks: ports match exactly, and params follow the operation's schema (T2.3, T2.6)."""

import pytest
from validator_samples import (
    REGISTRY,
    codes,
    definition,
    edge,
    file_input,
    node,
    output,
    reconcile_workflow,
)

from app.core.artifact_type import ArtifactType as T
from app.core.validator import validate
from app.core.workflow import InputContract, PortRef


def report(defn):
    return validate(defn, REGISTRY)


def test_matching_types_are_valid():
    assert report(reconcile_workflow()).valid


def test_no_implicit_conversion_from_text_to_table():
    defn = definition(
        [
            node("text", "extract_text"),
            node("table", "parse_csv"),
            node("cmp", "reconcile", key="k"),
        ],  # fmt: skip
        [edge("text", "cmp", "text", "left"), edge("table", "cmp", "table", "right")],
        [file_input("a", "text"), file_input("b", "table")],
    )
    [issue] = report(defn).errors
    assert (issue.code, issue.path, issue.node_id) == ("PORT_TYPE_MISMATCH", "edges/0", "cmp")
    assert issue.params == {
        "port": "left", "expected": "TabularArtifact", "got": "TextDocumentArtifact",
    }  # fmt: skip


def test_a_workflow_input_must_carry_the_port_type():
    tabular = InputContract(name="t", artifact_type=T.TABULAR,
                            targets=[PortRef(node_id="orders", port="file")])  # fmt: skip
    [issue] = report(definition([node("orders", "parse_csv")], [], [tabular])).errors
    assert (issue.code, issue.path) == ("PORT_TYPE_MISMATCH", "inputs/0/targets/0")
    assert issue.params == {"port": "file", "expected": "RawFile", "got": "TabularArtifact"}


def test_a_workflow_output_must_carry_the_port_type():
    defn = reconcile_workflow()
    wrong = defn.model_copy(update={"outputs": [output("r", "compare", "report", T.TABULAR)]})
    [issue] = report(wrong).errors
    assert (issue.code, issue.path) == ("PORT_TYPE_MISMATCH", "outputs/0/source")
    assert issue.params == {"port": "report", "expected": "TabularArtifact",
                            "got": "ComparisonReport"}  # fmt: skip


def _params_issues(**params):
    defn = reconcile_workflow()
    nodes = [*defn.nodes[:2], node("compare", "reconcile", **params)]
    found = report(defn.model_copy(update={"nodes": nodes})).errors
    return [(i.code, i.path, i.params) for i in found]


def test_valid_params_pass():
    assert _params_issues(key="order_id", tolerance="0.01", mode="fuzzy") == []


@pytest.mark.parametrize(
    ("params", "field", "rule"),
    [
        ({}, "key", "required"),
        ({"key": 3}, "key", "type"),
        ({"key": "id", "tolerance": "1,5"}, "tolerance", "pattern"),
        ({"key": "id", "mode": "loose"}, "mode", "enum"),
        ({"key": "id", "surprise": True}, "surprise", "additionalProperties"),
    ],
)
def test_invalid_params_give_param_invalid_with_the_field(params, field, rule):
    assert _params_issues(**params) == [
        ("PARAM_INVALID", f"nodes/2/params/{field}", {"field": field, "rule": rule})
    ]


def test_each_bad_field_is_its_own_issue():
    found = _params_issues(tolerance="x", mode="loose")
    assert sorted(path for _, path, _ in found) == [
        "nodes/2/params/key", "nodes/2/params/mode", "nodes/2/params/tolerance",
    ]  # fmt: skip


def test_a_mismatch_on_an_unknown_port_is_not_reported_twice():
    defn = definition([node("a"), node("b")], [edge("a", "b", "out", "nope")])
    assert codes(report(defn)) == ["PORT_UNKNOWN"]
