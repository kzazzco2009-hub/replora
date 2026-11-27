"""P3.6 cancellation between nodes (T3.6) and approval expiry (T3.7)."""

from datetime import timedelta
from uuid import uuid4

import pytest
from engine_samples import NOW, Spy, diamond, queued
from validator_samples import REGISTRY

from app.config import Settings
from app.core.engine.executor import execute
from app.core.engine.run import expire_if_stale, new_run, transition
from app.core.engine.store import ArtifactStore
from app.core.run_state import RunAction, RunState

TTL = timedelta(hours=24)


def run_it(run, spy, cancelled=lambda: False):
    return execute(
        run, REGISTRY, {("pass", 1): spy}, ArtifactStore(uuid4()), inputs={}, cancelled=cancelled
    )


def test_cancel_between_nodes_gives_cancelled_and_no_node_starts_after():
    spy = Spy()
    result = run_it(queued(diamond()), spy, cancelled=lambda: len(spy.calls) == 2)
    assert result.run.state is RunState.CANCELLED
    assert spy.calls == ["a", "c"]
    assert result.outputs == {}
    assert set(result.artifacts) == {("a", "out"), ("c", "out")}


def test_a_run_cancelled_while_queued_never_starts():
    spy = Spy()
    requested = transition(queued(diamond()), RunAction.CANCEL, NOW)
    assert requested.state is RunState.CANCEL_REQUESTED
    result = run_it(requested, spy)
    assert (result.run.state, spy.calls) == (RunState.CANCELLED, [])


def test_cancel_is_checked_before_the_first_node():
    spy = Spy()
    assert run_it(queued(diamond()), spy, cancelled=lambda: True).run.state is RunState.CANCELLED
    assert spy.calls == []


def awaiting(at=NOW):
    run = transition(new_run(diamond(), NOW), RunAction.VALIDATE, NOW)
    return transition(run, RunAction.REQUEST_APPROVAL, at)


def test_every_transition_records_when_the_state_began():
    later = NOW + timedelta(minutes=5)
    run = awaiting(at=later)
    assert (run.state_since, new_run(diamond(), NOW).state_since) == (later, NOW)


@pytest.mark.parametrize(
    ("age", "state"),
    [(TTL, RunState.AWAITING_APPROVAL), (TTL + timedelta(seconds=1), RunState.EXPIRED)],
)
def test_an_approval_older_than_the_ttl_expires(age, state):
    expired = expire_if_stale(awaiting(), NOW + age, TTL)
    assert expired.state is state
    if state is RunState.EXPIRED:
        assert expired.state_since == NOW + age


@pytest.mark.parametrize("state", [s for s in RunState if s is not RunState.AWAITING_APPROVAL])
def test_only_a_run_awaiting_approval_can_expire(state):
    run = awaiting().model_copy(update={"state": state})
    assert expire_if_stale(run, NOW + TTL * 10, TTL) is run


def test_the_ttl_is_configurable_and_defaults_to_24_hours():
    assert Settings().approval_ttl == TTL
    assert Settings(approval_ttl_hours=2).approval_ttl == timedelta(hours=2)
