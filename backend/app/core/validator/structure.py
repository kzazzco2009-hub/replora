"""Structural checks (P2.2): references, port bindings and cycles."""

from app.core.issue_codes import IssueCode
from app.core.validation import Issue
from app.core.validator.graph import Direction, Graph, issue, peel
from app.core.workflow import PortRef


def check(graph: Graph) -> list[Issue]:
    issues, bound = _references(graph)
    return [*issues, *_unbound(graph, bound), *_cycles(graph)]


def _ref(graph: Graph, ref: PortRef, path: str, direction: Direction) -> list[Issue]:
    if ref.node_id not in graph.positions:
        return [issue(IssueCode.NODE_UNKNOWN, f"{path}/node_id", node_id=ref.node_id)]
    ports = graph.ports(ref.node_id, direction)
    if ports is not None and ref.port not in ports:
        code, where = IssueCode.PORT_UNKNOWN, f"{path}/port"
        return [issue(code, where, ref.node_id, port=ref.port, direction=direction)]
    return []


def _references(graph: Graph) -> tuple[list[Issue], set[tuple[str, str]]]:
    """Every edge and IO reference, plus the input ports they bind."""
    issues: list[Issue] = []
    bound: set[tuple[str, str]] = set()

    def bind(ref: PortRef, path: str) -> None:
        found = _ref(graph, ref, path, "input")
        issues.extend(found)
        if found or graph.ports(ref.node_id, "input") is None:
            return
        if (ref.node_id, ref.port) in bound:
            issues.append(issue(IssueCode.PORT_BOUND_TWICE, path, ref.node_id, port=ref.port))
        bound.add((ref.node_id, ref.port))

    seen = set()
    for index, edge in enumerate(graph.definition.edges):
        key = (edge.source.node_id, edge.source.port, edge.target.node_id, edge.target.port)
        if key in seen:
            issues.append(issue(IssueCode.EDGE_DUPLICATE, f"edges/{index}", edge.target.node_id))
            continue
        seen.add(key)
        issues.extend(_ref(graph, edge.source, f"edges/{index}/source", "output"))
        bind(edge.target, f"edges/{index}/target")
    for index, contract in enumerate(graph.definition.inputs):
        for position, target in enumerate(contract.targets):
            bind(target, f"inputs/{index}/targets/{position}")
    for index, contract in enumerate(graph.definition.outputs):
        issues.extend(_ref(graph, contract.source, f"outputs/{index}/source", "output"))
    return issues, bound


def _unbound(graph: Graph, bound: set[tuple[str, str]]) -> list[Issue]:
    return [
        issue(IssueCode.PORT_UNBOUND, f"nodes/{graph.positions[node_id]}", node_id, port=port.name)
        for node_id, contract in graph.contracts.items()
        for port in contract.inputs
        if port.required and (node_id, port.name) not in bound
    ]


def _cycles(graph: Graph) -> list[Issue]:
    """Kahn forwards, then backwards, leaves exactly the nodes on (or between) cycles."""
    edges = graph.node_edges()
    stuck = peel(graph.positions, edges)
    on_cycle = peel(stuck, {(target, source) for source, target in edges})
    if not on_cycle:
        return []
    return [issue(IssueCode.DAG_CYCLE, "edges", nodes=sorted(on_cycle))]
