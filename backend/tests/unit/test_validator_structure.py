"""P2.2 structural checks and P2.5 version checks (T2.2, T2.4, T2.7, T2.8).

The validator never raises: every finding is an `Issue` in the report.
"""

from hypothesis import given, settings
from hypothesis import strategies as st
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

from app.core.validator import validate
from app.core.workflow import Edge, PortRef, WorkflowDefinition


def errors(defn: WorkflowDefinition) -> list[str]:
    return codes(validate(defn, REGISTRY))


def only(defn: WorkflowDefinition, code: str):
    report = validate(defn, REGISTRY)
    assert [issue.code for issue in report.errors] == [code], report.errors
    return report.errors[0]


def test_the_reconcile_workflow_is_valid():
    report = validate(reconcile_workflow(), REGISTRY)
    assert report.valid
    assert report.errors == []


def test_disconnected_subgraphs_are_valid():
    assert errors(definition([node("a"), node("b"), node("c")], [edge("a", "b")])) == []


def test_a_duplicate_node_id_is_reported_at_the_second_node():
    issue = only(definition([node("a"), node("a")]), "NODE_ID_DUPLICATE")
    assert (issue.path, issue.node_id) == ("nodes/1/id", "a")


# T2.2: cycles of every length, with the nodes involved.
def test_a_self_loop_is_a_cycle():
    issue = only(definition([node("a")], [edge("a", "a")]), "DAG_CYCLE")
    assert issue.params == {"nodes": ["a"]}


def test_a_two_cycle_is_a_cycle():
    issue = only(definition([node("a"), node("b")], [edge("a", "b"), edge("b", "a")]), "DAG_CYCLE")
    assert issue.params == {"nodes": ["a", "b"]}


def test_a_long_cycle_names_only_the_nodes_on_it():
    names = [f"n{k}" for k in range(6)]
    loop = [edge(a, b) for a, b in zip(names, names[1:] + names[:1], strict=True)]
    ends = [edge("before", "n0", "out", "in_1"), edge("n5", "after", "out", "in_1")]
    nodes = [*map(node, names), node("after"), node("before")]
    issue = only(definition(nodes, [*ends, *loop]), "DAG_CYCLE")
    assert issue.params == {"nodes": names}


# T2.4: unbound and unknown ports, unknown nodes.
def test_a_missing_required_input_is_port_unbound():
    issue = only(definition([node("compare", "reconcile", key="id"), node("a")],
                            [edge("a", "compare", "out", "left")]), "PORT_UNBOUND")  # fmt: skip
    assert (issue.path, issue.node_id, issue.params) == ("nodes/0", "compare", {"port": "right"})


def test_a_required_input_can_be_bound_by_a_workflow_input():
    assert errors(definition([node("orders", "parse_csv")], [], [file_input("f", "orders")])) == []


def test_an_edge_to_an_unknown_input_port_is_port_unknown():
    defn = definition([node("a"), node("b")], [edge("a", "b", "out", "nope")])
    issue = only(defn, "PORT_UNKNOWN")
    assert (issue.path, issue.node_id) == ("edges/0/target/port", "b")
    assert issue.params == {"port": "nope", "direction": "input"}


def test_an_edge_from_an_input_port_is_port_unknown():
    defn = definition([node("a"), node("b")], [edge("a", "b", "in_0", "in_0")])
    issue = only(defn, "PORT_UNKNOWN")
    assert issue.path == "edges/0/source/port"
    assert issue.params == {"port": "in_0", "direction": "output"}


def test_an_edge_to_an_unknown_node_is_node_unknown():
    issue = only(definition([node("a")], [edge("a", "ghost")]), "NODE_UNKNOWN")
    assert (issue.path, issue.params) == ("edges/0/target/node_id", {"node_id": "ghost"})


def test_workflow_inputs_and_outputs_must_point_at_real_ports():
    defn = definition(
        [node("orders", "parse_csv")],
        [],
        [file_input("f", "orders"), file_input("g", "ghost"), file_input("h", "orders", "nope")],
        [output("o", "orders", "nope")],
    )
    report = validate(defn, REGISTRY)
    found = sorted((i.code, i.path) for i in report.errors)
    assert found == [
        ("NODE_UNKNOWN", "inputs/1/targets/0/node_id"),
        ("PORT_UNKNOWN", "inputs/2/targets/0/port"),
        ("PORT_UNKNOWN", "outputs/0/source/port"),
    ]


def test_a_duplicate_edge_is_reported_once():
    issue = only(definition([node("a"), node("b")], [edge("a", "b"), edge("a", "b")]),
                 "EDGE_DUPLICATE")  # fmt: skip
    assert issue.path == "edges/1"


def test_an_input_port_fed_twice_is_port_bound_twice():
    defn = definition([node("a"), node("b"), node("c")], [edge("a", "c"), edge("b", "c")])
    issue = only(defn, "PORT_BOUND_TWICE")
    assert (issue.path, issue.node_id, issue.params) == ("edges/1/target", "c", {"port": "in_0"})


def test_one_output_may_feed_many_inputs():
    defn = definition([node("a"), node("b"), node("c")], [edge("a", "b"), edge("a", "c")])
    assert errors(defn) == []


# T2.7 (P2.5): unknown operations and versions.
def test_an_unknown_operation_is_op_unknown():
    issue = only(definition([node("a", "teleport")]), "OP_UNKNOWN")
    assert (issue.path, issue.node_id) == ("nodes/0/operation", "a")
    assert issue.params == {"operation": "teleport", "version": 1}


def test_an_unknown_version_is_op_version_invalid():
    issue = only(definition([node("a", "pass", version=2)]), "OP_VERSION_INVALID")
    assert issue.params == {"operation": "pass", "version": 2, "known": [1]}


def test_an_unpinned_version_is_op_version_invalid():
    for version in (0, -1):
        assert errors(definition([node("a", "pass", version=version)])) == ["OP_VERSION_INVALID"]


def test_ports_of_an_unresolved_node_are_not_reported_twice():
    defn = definition([node("a"), node("b", "teleport")], [edge("a", "b", "out", "anything")])
    assert errors(defn) == ["OP_UNKNOWN"]


# T2.8: random DAGs validate; one back-edge always fails. The validator never raises.
@st.composite
def dags(draw):
    size = draw(st.integers(1, 12))
    pairs = draw(st.lists(st.tuples(st.integers(0, size - 1), st.integers(0, size - 1))))
    seen, edges, used = set(), [], {}
    for a, b in pairs:
        low, high = sorted((a, b))
        if low == high or (low, high) in seen or used.get(high, 0) >= 10:
            continue
        seen.add((low, high))
        edges.append(edge(f"n{low}", f"n{high}", "out", f"in_{used.get(high, 0)}"))
        used[high] = used.get(high, 0) + 1
    return definition([node(f"n{k}") for k in range(size)], edges)


@settings(max_examples=200)
@given(dags())
def test_a_random_dag_is_valid(defn):
    assert errors(defn) == []


@settings(max_examples=200)
@given(dags(), st.data())
def test_a_back_edge_always_makes_a_cycle(defn, data):
    if not defn.edges:
        defn = definition(defn.nodes + [node("z")], [edge(defn.nodes[0].id, "z")])
    forward = data.draw(st.sampled_from(defn.edges))
    back = Edge(source=PortRef(node_id=forward.target.node_id, port="out"),
                target=PortRef(node_id=forward.source.node_id, port="in_11"))  # fmt: skip
    with_back = definition(defn.nodes, [*defn.edges, back])
    assert "DAG_CYCLE" in errors(with_back)


names = st.sampled_from(["a", "b", "c", "ghost"])
ports = st.sampled_from(["out", "in_0", "in_1", "file", "left", "nope"])
refs = st.builds(PortRef, node_id=names, port=ports)


@settings(max_examples=300)
@given(
    st.lists(st.builds(node, names, st.sampled_from(["pass", "parse_csv", "reconcile", "x"]),
                       st.integers(-1, 3)), max_size=5),
    st.lists(st.builds(Edge, source=refs, target=refs), max_size=8),
)  # fmt: skip
def test_the_validator_never_raises(nodes, edges):
    report = validate(definition(nodes, edges), REGISTRY)
    assert report.valid == (report.errors == [])
