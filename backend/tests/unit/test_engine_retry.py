"""P3.5 retry of transient errors only (T3.4) and idempotent nodes (T3.5)."""

from uuid import uuid4

from engine_samples import Spy, diamond, queued
from validator_samples import REGISTRY

from app.core.engine.executor import (
    BACKOFF_SECONDS,
    MAX_RETRIES,
    OperationError,
    TransientError,
    execute,
)
from app.core.engine.store import ArtifactStore
from app.core.run_issue_codes import RunIssueCode as R
from app.core.run_state import RunState


class Flaky(Spy):
    """`pass`, but node `b` raises `error` on its first `times` calls."""

    def __init__(self, error: OperationError, times: int) -> None:
        super().__init__()
        self.error, self.left = error, times

    def __call__(self, inputs, params):
        if params["tag"] == "b" and self.left:
            self.left -= 1
            self.calls.append("b!")
            raise self.error
        return super().__call__(inputs, params)


def run_it(spy, run=None, ledger=None, store=None):
    sleeps: list[float] = []
    result = execute(
        run or queued(diamond()), REGISTRY, {("pass", 1): spy}, store or ArtifactStore(uuid4()),
        inputs={}, ledger=ledger, sleep=sleeps.append,
    )  # fmt: skip
    return result, sleeps


def test_the_retry_policy_is_the_planned_one():
    assert MAX_RETRIES == 2


def test_a_transient_error_is_retried_with_backoff_and_can_recover():
    spy = Flaky(TransientError("UPSTREAM_BUSY"), times=2)
    result, sleeps = run_it(spy)
    assert result.run.state is RunState.SUCCEEDED
    assert spy.calls.count("b!") == 2
    assert spy.calls.count("b") == 1
    assert sleeps == [BACKOFF_SECONDS, BACKOFF_SECONDS * 2]


def test_a_transient_error_gets_at_most_two_extra_attempts():
    spy = Flaky(TransientError("UPSTREAM_BUSY"), times=5)
    result, sleeps = run_it(spy)
    assert spy.calls.count("b!") == 1 + MAX_RETRIES
    assert len(sleeps) == MAX_RETRIES
    assert [(i.code, i.node_id) for i in result.issues] == [(R.NODE_FAILED, "b")]
    assert result.issues[0].params == {"error": "UPSTREAM_BUSY", "attempts": 3}


def test_a_non_transient_error_is_never_retried():
    spy = Flaky(OperationError("CSV_UNREADABLE"), times=5)
    result, sleeps = run_it(spy)
    assert (spy.calls.count("b!"), sleeps) == (1, [])
    assert result.issues[0].params == {"error": "CSV_UNREADABLE", "attempts": 1}


def test_a_node_is_not_executed_twice_for_the_same_inputs():
    spy, ledger, store, run = Spy(), {}, ArtifactStore(uuid4()), queued(diamond())
    first, _ = run_it(spy, run, ledger, store)
    again, _ = run_it(spy, run, ledger, store)
    assert spy.calls == ["a", "c", "b", "d"]
    assert again.run.state is RunState.SUCCEEDED
    assert again.outputs == first.outputs


def test_the_key_includes_the_run():
    spy, ledger, store = Spy(), {}, ArtifactStore(uuid4())
    run_it(spy, queued(diamond()), ledger, store)
    run_it(spy, queued(diamond()), ledger, store)
    assert spy.calls == ["a", "c", "b", "d"] * 2


def test_a_failed_node_is_not_recorded_so_a_later_attempt_runs_it():
    spy, ledger, store = Flaky(OperationError("X"), times=1), {}, ArtifactStore(uuid4())
    run = queued(diamond())
    first, _ = run_it(spy, run, ledger, store)
    again, _ = run_it(spy, run, ledger, store)
    assert first.run.state is RunState.PARTIAL
    assert again.run.state is RunState.SUCCEEDED
    assert spy.calls == ["a", "c", "b!", "d", "b", "d"]
