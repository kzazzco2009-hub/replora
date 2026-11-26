"""The in-memory executor (P3.3): nodes run one at a time in topological order.

It runs a definition the validator (P2) has already accepted, so every port is bound and there
is no cycle. Each output is stored as an artifact whose lineage names the run, the node, the
operation version and the artifacts it was made from.
"""

import heapq
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from pydantic import JsonValue

from app.core.artifacts import ArtifactLineage, ArtifactRef
from app.core.engine.run import Run, transition
from app.core.engine.store import ArtifactStore, Data
from app.core.registry import OperationRegistry
from app.core.run_state import RunAction
from app.core.workflow import Node, WorkflowDefinition

Handler = Callable[[Mapping[str, Data], Mapping[str, JsonValue]], Mapping[str, Data]]
"""An operation's implementation: input data by port name and the params, to output data."""

Handlers = Mapping[tuple[str, int], Handler]
Slot = tuple[str, str]
"""A `(node_id, port)` pair."""


@dataclass(frozen=True)
class Execution:
    run: Run
    artifacts: dict[Slot, ArtifactRef]
    """Every artifact the run produced, by the output port that made it."""
    outputs: dict[str, ArtifactRef]
    """The workflow's outputs, by output contract name."""


def topological_order(definition: WorkflowDefinition) -> list[str]:
    """Kahn's algorithm. Among the nodes that are ready, the first in the definition runs first."""
    position = {node.id: index for index, node in enumerate(definition.nodes)}
    pairs = {(e.source.node_id, e.target.node_id) for e in definition.edges}
    indegree = dict.fromkeys(position, 0)
    for _, target in pairs:
        indegree[target] += 1
    ready = [(position[n], n) for n, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        _, current = heapq.heappop(ready)
        order.append(current)
        for source, target in pairs:
            if source == current:
                indegree[target] -= 1
                if indegree[target] == 0:
                    heapq.heappush(ready, (position[target], target))
    return order


def execute(
    run: Run,
    registry: OperationRegistry,
    handlers: Handlers,
    store: ArtifactStore,
    inputs: Mapping[str, ArtifactRef],
) -> Execution:
    """Run an approved, queued run to the end. `inputs` are the workflow's files by name."""
    run = transition(run, RunAction.START)
    definition = run.definition
    feeds = {(t.node_id, t.port): inputs[i.name] for i in definition.inputs for t in i.targets}
    wires = {(e.target.node_id, e.target.port): (e.source.node_id, e.source.port)
             for e in definition.edges}  # fmt: skip
    nodes = {node.id: node for node in definition.nodes}
    produced: dict[Slot, ArtifactRef] = {}
    for node_id in topological_order(definition):
        bound = {port: ref for (target, port), ref in feeds.items() if target == node_id}
        bound |= {port: produced[source] for (target, port), source in wires.items()
                  if target == node_id}  # fmt: skip
        produced |= _run_node(run, nodes[node_id], bound, registry, handlers, store)
    outputs = {o.name: produced[o.source.node_id, o.source.port] for o in definition.outputs}
    return Execution(transition(run, RunAction.SUCCEED), produced, outputs)


def _run_node(
    run: Run,
    node: Node,
    bound: dict[str, ArtifactRef],
    registry: OperationRegistry,
    handlers: Handlers,
    store: ArtifactStore,
) -> dict[Slot, ArtifactRef]:
    contract = registry.get(node.operation.id, node.operation.version)
    handler = handlers[node.operation.id, node.operation.version]
    result = handler({port: store.read(ref) for port, ref in bound.items()}, node.params)
    lineage = ArtifactLineage(
        run_id=run.id,
        node_id=node.id,
        operation=node.operation,
        parents=[ref.id for _, ref in sorted(bound.items())],
    )
    return {
        (node.id, port.name): store.put(result[port.name], port.artifact_type, lineage)
        for port in contract.outputs
    }
