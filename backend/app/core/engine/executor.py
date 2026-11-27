"""The in-memory executor (P3.3, P3.4): nodes run one at a time in topological order.

It runs a definition the validator (P2) has already accepted, so every port is bound and there
is no cycle. Each output is stored as an artifact whose lineage names the run, the node, the
operation version and the artifacts it was made from.

A node that raises `OperationError` fails, and a node missing a required input is skipped. The run
is FAILED when a workflow output is missing, PARTIAL when something failed but every output
exists, and NEEDS_REVIEW as soon as a node warns under the `review` policy.
"""

import heapq
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from pydantic import JsonValue

from app.core.artifacts import ArtifactLineage, ArtifactRef
from app.core.engine.run import Run, transition
from app.core.engine.store import ArtifactStore, Data
from app.core.registry import OperationRegistry
from app.core.run_issue_codes import RunIssueCode
from app.core.run_state import RunAction
from app.core.validation import Issue
from app.core.workflow import WorkflowDefinition

Slot = tuple[str, str]
"""A `(node_id, port)` pair."""


class OperationError(Exception):
    """An operation couldn't produce its outputs. `code` and `params` go into the issue."""

    def __init__(self, code: str, **params: Any) -> None:
        self.code = code
        self.params = params
        super().__init__(code)


@dataclass(frozen=True)
class Result:
    """What a handler gives: data by output port, and any warnings about it."""

    outputs: Mapping[str, Data]
    warnings: Sequence[Issue] = ()


Handler = Callable[[Mapping[str, Data], Mapping[str, JsonValue]], Result]
"""An operation's implementation: input data by port name and the params, to a `Result`."""

Handlers = Mapping[tuple[str, int], Handler]


@dataclass(frozen=True)
class Execution:
    run: Run
    artifacts: dict[Slot, ArtifactRef]
    """Every artifact the run produced, by the output port that made it."""
    outputs: dict[str, ArtifactRef]
    """The workflow's outputs, by output contract name."""
    issues: list[Issue] = field(default_factory=list)
    """Failures, skips and warnings, in the order they happened."""


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
    """Run an approved, queued run to its end state. `inputs` are the workflow's files by name."""
    return _Runner(transition(run, RunAction.START), registry, handlers, store).run(inputs)


@dataclass
class _Runner:
    run_: Run
    registry: OperationRegistry
    handlers: Handlers
    store: ArtifactStore
    produced: dict[Slot, ArtifactRef] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)

    def run(self, inputs: Mapping[str, ArtifactRef]) -> Execution:
        definition = self.run_.definition
        feeds = {(t.node_id, t.port): inputs[i.name] for i in definition.inputs for t in i.targets}
        wires = {(e.target.node_id, e.target.port): (e.source.node_id, e.source.port)
                 for e in definition.edges}  # fmt: skip
        for node_id in topological_order(definition):
            if not self._node(node_id, feeds, wires):
                return self._end(RunAction.REQUEST_REVIEW)
        return self._end(self._outcome())

    def _node(self, node_id: str, feeds: dict, wires: dict) -> bool:
        """Run one node. False when its warnings stop the run for review."""
        index, node = next((i, n) for i, n in enumerate(self.run_.definition.nodes)
                           if n.id == node_id)  # fmt: skip
        path = f"nodes/{index}"
        contract = self.registry.get(node.operation.id, node.operation.version)
        bound = {port: ref for (target, port), ref in feeds.items() if target == node_id}
        for (target, port), source in wires.items():
            if target == node_id and source in self.produced:
                bound[port] = self.produced[source]
        for port in contract.inputs:
            if port.required and port.name not in bound:
                source = wires[node_id, port.name][0]
                self._issue(RunIssueCode.NODE_SKIPPED, path, node_id, port=port.name, source=source)
                return True
        handler = self.handlers[node.operation.id, node.operation.version]
        try:
            result = handler({p: self.store.read(r) for p, r in bound.items()}, node.params)
        except OperationError as error:
            self._issue(RunIssueCode.NODE_FAILED, path, node_id, error=error.code, **error.params)
            return True
        lineage = ArtifactLineage(run_id=self.run_.id, node_id=node_id, operation=node.operation,
                                  parents=[ref.id for _, ref in sorted(bound.items())])  # fmt: skip
        for port in contract.outputs:
            ref = self.store.put(result.outputs[port.name], port.artifact_type, lineage)
            self.produced[node_id, port.name] = ref
        for warning in result.warnings:
            self._issue(warning.code, f"{path}/{warning.path}", node_id, **warning.params)
        policy = self.run_.definition.review_policy.on_warning
        return not (result.warnings and policy == "review")

    def _outcome(self) -> RunAction:
        for index, out in enumerate(self.run_.definition.outputs):
            if (out.source.node_id, out.source.port) not in self.produced:
                self._issue(RunIssueCode.OUTPUT_MISSING, f"outputs/{index}", None, output=out.name)
        codes = {issue.code for issue in self.issues}
        if RunIssueCode.OUTPUT_MISSING in codes:
            return RunAction.FAIL
        if codes & {RunIssueCode.NODE_FAILED, RunIssueCode.NODE_SKIPPED}:
            return RunAction.FINISH_PARTIAL
        return RunAction.SUCCEED

    def _issue(self, code: str, path: str, node_id: str | None, **params: Any) -> None:
        self.issues.append(Issue(code=code, path=path, node_id=node_id, params=params))

    def _end(self, action: RunAction) -> Execution:
        outputs = {o.name: self.produced[o.source.node_id, o.source.port]
                   for o in self.run_.definition.outputs
                   if (o.source.node_id, o.source.port) in self.produced}  # fmt: skip
        return Execution(transition(self.run_, action), self.produced, outputs, self.issues)
