"""A definition with its nodes indexed and their operations resolved, for the checks."""

from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Literal

from app.core.issue_codes import IssueCode
from app.core.operations import OperationContract, Port
from app.core.registry import OperationRegistry, RegistryError
from app.core.validation import Issue
from app.core.workflow import WorkflowDefinition

Direction = Literal["input", "output"]


def issue(code: IssueCode, path: str, node: str | None = None, **params: Any) -> Issue:
    return Issue(code=code, path=path, node_id=node, params=params)


@dataclass(frozen=True)
class Graph:
    definition: WorkflowDefinition
    positions: dict[str, int]
    """The index of each node ID's first occurrence."""
    contracts: dict[str, OperationContract]
    """Only the nodes whose operation version resolved."""
    issues: list[Issue]

    @classmethod
    def build(cls, definition: WorkflowDefinition, registry: OperationRegistry) -> Graph:
        positions: dict[str, int] = {}
        contracts: dict[str, OperationContract] = {}
        issues: list[Issue] = []
        for index, node in enumerate(definition.nodes):
            if node.id in positions:
                issues.append(issue(IssueCode.NODE_ID_DUPLICATE, f"nodes/{index}/id", node.id))
                continue
            positions[node.id] = index
            try:
                contracts[node.id] = registry.get(node.operation.id, node.operation.version)
            except RegistryError as error:
                path = f"nodes/{index}/operation"
                issues.append(issue(IssueCode(error.code), path, node.id, **error.params))
        return cls(definition, positions, contracts, issues)

    def ports(self, node_id: str, direction: Direction) -> dict[str, Port] | None:
        """The node's ports by name, or None when its operation didn't resolve."""
        contract = self.contracts.get(node_id)
        if contract is None:
            return None
        return {port.name: port for port in getattr(contract, f"{direction}s")}

    def node_edges(self) -> set[tuple[str, str]]:
        """Distinct `(source, target)` node pairs between known nodes."""
        return {
            (edge.source.node_id, edge.target.node_id)
            for edge in self.definition.edges
            if edge.source.node_id in self.positions and edge.target.node_id in self.positions
        }


def peel(nodes: Iterable[str], edges: set[tuple[str, str]]) -> set[str]:
    """Kahn's algorithm: the nodes left after removing every node with no incoming edge."""
    indegree = dict.fromkeys(nodes, 0)
    after = defaultdict(list)
    for source, target in edges:
        if source in indegree and target in indegree:
            indegree[target] += 1
            after[source].append(target)
    ready = deque(node for node, count in indegree.items() if count == 0)
    while ready:
        node = ready.popleft()
        del indegree[node]
        for target in after[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return set(indegree)
