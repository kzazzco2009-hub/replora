"""P2.6: every validator error has a stable code and a location the frontend can point at.

There is one scenario per `IssueCode`, so a new code can't be added without one.
"""

import pytest
from validator_samples import REGISTRY, definition, edge, file_input, node, reconcile_workflow

from app.core.issue_codes import IssueCode as C
from app.core.validator import validate
from app.core.workflow import ResourcePolicy

ok = reconcile_workflow()
no_key = ok.model_copy(update={"nodes": [*ok.nodes[:2], node("compare", "reconcile")]})
fan_in = [edge(f"s{k}", "t", "out", f"in_{k}") for k in range(11)]
SCENARIOS = {
    C.OP_UNKNOWN: (definition([node("a", "teleport")]), ()),
    C.OP_VERSION_INVALID: (definition([node("a", version=9)]), ()),
    C.NODE_ID_DUPLICATE: (definition([node("a"), node("a")]), ()),
    C.NODE_UNKNOWN: (definition([node("a")], [edge("a", "ghost")]), ()),
    C.PORT_UNKNOWN: (definition([node("a"), node("b")], [edge("a", "b", "out", "x")]), ()),
    C.PORT_UNBOUND: (definition([node("p", "parse_csv")]), ()),
    C.PORT_BOUND_TWICE: (
        definition([node("a"), node("b"), node("c")], [edge("a", "c"), edge("b", "c")]),
        (),
    ),
    C.EDGE_DUPLICATE: (definition([node("a"), node("b")], [edge("a", "b"), edge("a", "b")]), ()),
    C.DAG_CYCLE: (definition([node("a")], [edge("a", "a")]), ()),
    C.PORT_TYPE_MISMATCH: (
        definition(
            [node("t", "extract_text"), node("x")],
            [edge("t", "x", "text", "in_0")],
            [file_input("f", "t")],
        ),
        (),
    ),  # fmt: skip
    C.PARAM_INVALID: (no_key, ()),
    C.LIMIT_NODES: (definition(node(f"n{k}") for k in range(31)), ()),
    C.LIMIT_DEPTH: (
        definition(
            [node(f"n{k}") for k in range(11)], [edge(f"n{k}", f"n{k + 1}") for k in range(10)]
        ),
        (),
    ),  # fmt: skip
    C.LIMIT_FAN_IN: (definition([*(node(f"s{k}") for k in range(11)), node("t")], fan_in), ()),
    C.LIMIT_FAN_OUT: (
        definition(
            [node("s"), *(node(f"t{k}") for k in range(11))],
            [edge("s", f"t{k}") for k in range(11)],
        ),
        (),
    ),  # fmt: skip
    C.LIMIT_FILES: (ok.model_copy(update={"resource_policy": ResourcePolicy(max_files=1)}), ()),
    C.LIMIT_FILE_SIZE: (ok, (51 * 1024 * 1024,)),
}
NODE_SCOPED = {C.OP_UNKNOWN, C.OP_VERSION_INVALID, C.NODE_ID_DUPLICATE, C.PORT_UNKNOWN,
               C.PORT_UNBOUND, C.PORT_BOUND_TWICE, C.PORT_TYPE_MISMATCH, C.PARAM_INVALID,
               C.LIMIT_FAN_IN, C.LIMIT_FAN_OUT}  # fmt: skip
PORT_SCOPED = {C.PORT_UNKNOWN, C.PORT_UNBOUND, C.PORT_BOUND_TWICE, C.PORT_TYPE_MISMATCH}


def test_every_code_has_a_scenario():
    assert set(SCENARIOS) == set(C)


def _resolves(document, path: str) -> bool:
    """Whether every segment of `path` but the last exists in `document`."""
    node = document
    for segment in path.split("/")[:-1]:
        if isinstance(node, list) and segment.isdigit() and int(segment) < len(node):
            node = node[int(segment)]
        elif isinstance(node, dict) and segment in node:
            node = node[segment]
        else:
            return False
    return True


@pytest.mark.parametrize("code", list(C))
def test_each_code_is_reported_with_its_location(code):
    defn, sizes = SCENARIOS[code]
    report = validate(defn, REGISTRY, file_sizes=sizes)
    found = [issue for issue in report.errors if issue.code == code]
    assert found, report.errors
    document = defn.model_dump(mode="json")
    for issue in found:
        assert issue.path.startswith("files") or _resolves(document, issue.path), issue.path
        if code in NODE_SCOPED:
            assert issue.node_id in {n.id for n in defn.nodes}
        if code in PORT_SCOPED:
            assert issue.params["port"]
