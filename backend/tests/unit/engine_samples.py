"""Fake handlers and run builders for the engine tests (Phase 3)."""

from datetime import UTC, datetime
from uuid import uuid4

from validator_samples import definition, edge, node, output

from app.core.artifact_type import ArtifactType as T
from app.core.engine.executor import OperationError, Result
from app.core.engine.run import approve, new_run, transition
from app.core.engine.store import Data
from app.core.run_state import RunAction
from app.core.validation import Issue

NOW = datetime(2026, 11, 26, 12, tzinfo=UTC)


def diamond(**policies):
    """a fans out to b and c, which fan in to d. Listed out of order on purpose."""
    return definition(
        [node("d", tag="d"), node("c", tag="c"), node("b", tag="b"), node("a", tag="a")],
        [edge("a", "b"), edge("a", "c"), edge("b", "d", "out", "in_0"),
         edge("c", "d", "out", "in_1")],
        outputs=[output("result", "d", "out", T.TABULAR)],
        **policies,
    )  # fmt: skip


class Spy:
    """The `pass` handler: its tag, then its inputs in port order. Records the call order.

    `fail` and `warn` name the tags that raise an `OperationError` or report `LOW_CONFIDENCE`.
    """

    def __init__(self, fail=(), warn=()) -> None:
        self.calls: list[str] = []
        self.fail, self.warn = set(fail), set(warn)

    def __call__(self, inputs, params):
        tag = params["tag"]
        self.calls.append(tag)
        if tag in self.fail:
            raise OperationError("CSV_UNREADABLE", row=3)
        joined = b"".join(inputs[port].content for port in sorted(inputs))
        out = Data(content=tag.encode() + b"(" + joined + b")", format="csv")
        warnings = [Issue(code="LOW_CONFIDENCE", path="out")] if tag in self.warn else []
        return Result(outputs={"out": out}, warnings=warnings)


def queued(defn):
    run = transition(transition(new_run(defn, NOW), RunAction.VALIDATE), RunAction.REQUEST_APPROVAL)
    return approve(run, run.plan_hash, uuid4(), NOW)
