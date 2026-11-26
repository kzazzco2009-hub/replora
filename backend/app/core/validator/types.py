"""Type checks (P2.3): artifact types match exactly at every port, and params fit their schema.

There is no implicit conversion: a `TextDocumentArtifact` never feeds a `TabularArtifact` port.
A param issue names the field and the JSON Schema keyword it broke, never the library's message.
"""

from typing import Any

from jsonschema import Draft202012Validator

from app.core.artifact_type import ArtifactType
from app.core.issue_codes import IssueCode
from app.core.validation import Issue
from app.core.validator.graph import Direction, Graph, issue
from app.core.workflow import PortRef


def check(graph: Graph) -> list[Issue]:
    return [*_ports(graph), *_params(graph)]


def _mismatch(graph: Graph, ref: PortRef, direction: Direction, got: ArtifactType, path: str):
    port = (graph.ports(ref.node_id, direction) or {}).get(ref.port)
    if port is None or port.artifact_type == got:
        return []
    expected = port.artifact_type if direction == "input" else got
    actual = got if direction == "input" else port.artifact_type
    code = IssueCode.PORT_TYPE_MISMATCH
    return [issue(code, path, ref.node_id, port=ref.port, expected=expected, got=actual)]


def _ports(graph: Graph) -> list[Issue]:
    found: list[Issue] = []
    definition = graph.definition
    for index, edge in enumerate(definition.edges):
        source = (graph.ports(edge.source.node_id, "output") or {}).get(edge.source.port)
        if source is not None:
            path = f"edges/{index}"
            found += _mismatch(graph, edge.target, "input", source.artifact_type, path)
    for index, contract in enumerate(definition.inputs):
        for position, target in enumerate(contract.targets):
            path = f"inputs/{index}/targets/{position}"
            found += _mismatch(graph, target, "input", contract.artifact_type, path)
    for index, contract in enumerate(definition.outputs):
        path = f"outputs/{index}/source"
        found += _mismatch(graph, contract.source, "output", contract.artifact_type, path)
    return found


def _params(graph: Graph) -> list[Issue]:
    found = []
    for node_id, contract in graph.contracts.items():
        index = graph.positions[node_id]
        params = graph.definition.nodes[index].params
        for field, rule in _broken(contract.params_schema, params):
            path = f"nodes/{index}/params/{field}"
            found.append(issue(IssueCode.PARAM_INVALID, path, node_id, field=field, rule=rule))
    return found


def _broken(schema: dict[str, Any], params: dict[str, Any]) -> list[tuple[str, str]]:
    """`(field, keyword)` for each broken rule, one per field, in field order."""
    broken = {field: "required" for field in schema.get("required", []) if field not in params}
    if schema.get("additionalProperties") is False:
        known = schema.get("properties", {})
        broken |= {field: "additionalProperties" for field in params if field not in known}
    for error in Draft202012Validator(schema).iter_errors(params):
        if error.absolute_path:
            broken.setdefault(str(error.absolute_path[0]), str(error.validator))
    return sorted(broken.items())
