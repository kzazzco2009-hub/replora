"""Limit checks (P2.4, S-12): size and shape of the graph, and the files a run would read."""

from collections import Counter, defaultdict, deque
from collections.abc import Sequence

from app.core.issue_codes import IssueCode
from app.core.limits import MAX_DEPTH, MAX_FAN_IN, MAX_FAN_OUT, MAX_NODES
from app.core.validation import Issue
from app.core.validator.graph import Graph, issue


def check(graph: Graph, file_sizes: Sequence[int]) -> list[Issue]:
    return [*_shape(graph), *_fans(graph), *_files(graph, file_sizes)]


def _over(code: IssueCode, path: str, limit: int, actual: int, node: str | None = None):
    return [issue(code, path, node, limit=limit, actual=actual)] if actual > limit else []


def _shape(graph: Graph) -> list[Issue]:
    found = _over(IssueCode.LIMIT_NODES, "nodes", MAX_NODES, len(graph.definition.nodes))
    depth = _depth(graph)
    if depth is not None:
        found += _over(IssueCode.LIMIT_DEPTH, "edges", MAX_DEPTH, depth)
    return found


def _depth(graph: Graph) -> int | None:
    """Nodes on the longest path, or None when there is a cycle (that is `DAG_CYCLE`)."""
    edges = graph.node_edges()
    indegree = Counter(target for _, target in edges)
    after = defaultdict(list)
    for source, target in edges:
        after[source].append(target)
    longest = dict.fromkeys(graph.positions, 1)
    ready = deque(node for node in graph.positions if not indegree[node])
    done = 0
    while ready:
        node = ready.popleft()
        done += 1
        for target in after[node]:
            longest[target] = max(longest[target], longest[node] + 1)
            indegree[target] -= 1
            if not indegree[target]:
                ready.append(target)
    if done < len(graph.positions):
        return None
    return max(longest.values(), default=0)


def _fans(graph: Graph) -> list[Issue]:
    edges = {(e.source.node_id, e.source.port, e.target.node_id, e.target.port)
             for e in graph.definition.edges}  # fmt: skip
    fan_out = Counter(source for source, _, _, _ in edges)
    fan_in = Counter(target for _, _, target, _ in edges)
    found = []
    for node, index in graph.positions.items():
        path = f"nodes/{index}"
        found += _over(IssueCode.LIMIT_FAN_IN, path, MAX_FAN_IN, fan_in[node], node)
        found += _over(IssueCode.LIMIT_FAN_OUT, path, MAX_FAN_OUT, fan_out[node], node)
    return found


def _files(graph: Graph, file_sizes: Sequence[int]) -> list[Issue]:
    policy = graph.definition.resource_policy
    found = _over(IssueCode.LIMIT_FILES, "inputs", policy.max_files, len(graph.definition.inputs))
    found += _over(IssueCode.LIMIT_FILES, "files", policy.max_files, len(file_sizes))
    for index, size in enumerate(file_sizes):
        found += _over(IssueCode.LIMIT_FILE_SIZE, f"files/{index}", policy.max_file_size, size)
    return found
