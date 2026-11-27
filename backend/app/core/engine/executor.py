"""The in-memory executor (P3.3–P3.5): nodes run one at a time in topological order.

It runs a definition the validator (P2) has already accepted, so every port is bound and there
is no cycle. Each output is stored as an artifact whose lineage names the run, the node, the
operation version and the artifacts it was made from.

A node that raises `OperationError` fails, and a node missing a required input is skipped. The run
is FAILED when a workflow output is missing, PARTIAL when something failed but every output
exists, and NEEDS_REVIEW as soon as a node warns under the `review` policy.

Only a `TransientError` is retried: at most `MAX_RETRIES` more times, with exponential backoff.
A node that succeeded is recorded in the ledger under `(run_id, node_id, input hashes)`, so it is
never executed twice for the same inputs.
"""

import heapq
import itertools
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from pydantic import JsonValue

from app.core.artifacts import ArtifactLineage, ArtifactRef
from app.core.engine.run import Run, check_approval, transition
from app.core.engine.store import Data, Store
from app.core.registry import OperationRegistry
from app.core.run_issue_codes import RunIssueCode
from app.core.run_state import RunAction, RunState
from app.core.validation import Issue
from app.core.workflow import Node, WorkflowDefinition

MAX_RETRIES = 2
BACKOFF_SECONDS = 0.5

Slot = tuple[str, str]
"""A `(node_id, port)` pair."""

NodeKey = tuple[UUID, str, tuple[tuple[str, str], ...]]
"""The idempotency key: run, node, and the SHA-256 of each input by port."""


class OperationError(Exception):
    """An operation couldn't produce its outputs. `code` and `params` go into the issue."""

    def __init__(self, code: str, **params: Any) -> None:
        self.code = code
        self.params = params
        super().__init__(code)


class TransientError(OperationError):
    """A failure that may pass on its own, for example a busy service. It is retried."""


@dataclass(frozen=True)
class Result:
    """What a handler gives: data by output port, and any warnings about it."""

    outputs: Mapping[str, Data]
    warnings: Sequence[Issue] = ()


@dataclass(frozen=True)
class Done:
    """A node that succeeded: its artifacts by output port, and its warnings."""

    outputs: dict[str, ArtifactRef]
    warnings: Sequence[Issue]


Handler = Callable[[Mapping[str, Data], Mapping[str, JsonValue]], Result]
"""An operation's implementation: input data by port name and the params, to a `Result`."""

Handlers = Mapping[tuple[str, int], Handler]


class Ledger(Protocol):
    """The nodes already done, by idempotency key: a dict in memory, `run_nodes` in the DB."""

    def __contains__(self, key: object) -> bool: ...
    def __getitem__(self, key: NodeKey) -> Done: ...
    def __setitem__(self, key: NodeKey, done: Done) -> None: ...


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
    store: Store,
    inputs: Mapping[str, ArtifactRef],
    ledger: Ledger | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    cancelled: Callable[[], bool] = lambda: False,
    checkpoint: Callable[[Run], None] = lambda run: None,
) -> Execution:
    """Run an approved, queued run to its end state. `inputs` are the workflow's files by name.

    Pass the same `ledger` to a later attempt of the same run to skip the nodes already done. A
    run that is already RUNNING (its worker died) resumes instead of starting again.
    `cancelled` is asked before every node; once it says yes, no other node starts.
    `checkpoint` gets the run when it starts and ends (P4.6). Nodes and artifacts are saved by
    the ledger and the store as each node finishes.
    """
    if run.state is RunState.CANCEL_REQUESTED:
        cancelled_run = transition(run, RunAction.CONFIRM_CANCEL, clock())
        checkpoint(cancelled_run)
        return Execution(cancelled_run, {}, {})
    if run.state is RunState.RUNNING:
        check_approval(run)
    else:
        run = transition(run, RunAction.START, clock())
    checkpoint(run)
    runner = _Runner(run, registry, handlers, store, {} if ledger is None else ledger, sleep,
                     clock, cancelled, checkpoint)  # fmt: skip
    return runner.run(inputs)


@dataclass
class _Runner:
    run_: Run
    registry: OperationRegistry
    handlers: Handlers
    store: Store
    ledger: Ledger
    sleep: Callable[[float], None]
    clock: Callable[[], datetime]
    cancelled: Callable[[], bool]
    checkpoint: Callable[[Run], None]
    produced: dict[Slot, ArtifactRef] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)

    def run(self, inputs: Mapping[str, ArtifactRef]) -> Execution:
        definition = self.run_.definition
        feeds = {(t.node_id, t.port): inputs[i.name] for i in definition.inputs for t in i.targets}
        wires = {(e.target.node_id, e.target.port): (e.source.node_id, e.source.port)
                 for e in definition.edges}  # fmt: skip
        index = {node.id: i for i, node in enumerate(definition.nodes)}
        for node_id in topological_order(definition):
            if self.cancelled():
                self.run_ = transition(self.run_, RunAction.CANCEL, self.clock())
                return self._end(RunAction.CONFIRM_CANCEL)
            node = definition.nodes[index[node_id]]
            if not self._node(node, f"nodes/{index[node_id]}", feeds, wires):
                return self._end(RunAction.REQUEST_REVIEW)
        return self._end(self._outcome())

    def _node(self, node: Node, path: str, feeds: dict, wires: dict) -> bool:
        """Run one node. False when its warnings stop the run for review."""
        contract = self.registry.get(node.operation.id, node.operation.version)
        bound = {port: ref for (target, port), ref in feeds.items() if target == node.id}
        for (target, port), source in wires.items():
            if target == node.id and source in self.produced:
                bound[port] = self.produced[source]
        for port in contract.inputs:
            if port.required and port.name not in bound:
                source = wires[node.id, port.name][0]
                self._issue(RunIssueCode.NODE_SKIPPED, path, node.id, port=port.name, source=source)
                return True
        key = (self.run_.id, node.id, tuple(sorted((p, r.sha256) for p, r in bound.items())))
        if key not in self.ledger:
            try:
                self.ledger[key] = self._call(node, bound, contract.outputs)
            except _Failed as failed:
                self._issue(RunIssueCode.NODE_FAILED, path, node.id, **failed.params)
                return True
        done = self.ledger[key]
        self.produced |= {(node.id, port): ref for port, ref in done.outputs.items()}
        for warning in done.warnings:
            self._issue(warning.code, f"{path}/{warning.path}", node.id, **warning.params)
        return not (done.warnings and self.run_.definition.review_policy.on_warning == "review")

    def _call(self, node: Node, bound: dict[str, ArtifactRef], ports) -> Done:
        """Call the handler, retrying a transient error, and store what it gives."""
        handler = self.handlers[node.operation.id, node.operation.version]
        data = {port: self.store.read(ref) for port, ref in bound.items()}
        for attempt in itertools.count(1):
            try:
                result = handler(data, node.params)
                break
            except TransientError as error:
                if attempt > MAX_RETRIES:
                    raise _Failed(error, attempt) from error
                self.sleep(BACKOFF_SECONDS * 2 ** (attempt - 1))
            except OperationError as error:
                raise _Failed(error, attempt) from error
        lineage = ArtifactLineage(run_id=self.run_.id, node_id=node.id, operation=node.operation,
                                  parents=[ref.id for _, ref in sorted(bound.items())])  # fmt: skip
        outputs = {p.name: self.store.put(result.outputs[p.name], p.artifact_type, lineage)
                   for p in ports}  # fmt: skip
        return Done(outputs, result.warnings)

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
        end = transition(self.run_, action, self.clock())
        self.checkpoint(end)
        return Execution(end, self.produced, outputs, self.issues)


class _Failed(Exception):
    """A node's last attempt failed."""

    def __init__(self, error: OperationError, attempts: int) -> None:
        self.params = {"error": error.code, "attempts": attempts, **error.params}
