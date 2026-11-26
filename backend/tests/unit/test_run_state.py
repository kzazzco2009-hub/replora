"""P1.5 run lifecycle as data: every state pair the table doesn't list is rejected (T1.5)."""

from itertools import product

import pytest

from app.api.v1 import run_models
from app.core.run_state import (
    TERMINAL_STATES,
    TRANSITIONS,
    InvalidTransitionError,
    RunAction,
    RunState,
    can_move,
    next_state,
)

S = RunState
# Written out by hand from docs/api_contract.md §7, not derived from the table under test.
ALLOWED = {
    (S.DRAFT, S.VALIDATED),
    (S.VALIDATED, S.AWAITING_APPROVAL),
    (S.VALIDATED, S.NEEDS_REVIEW),
    (S.AWAITING_APPROVAL, S.QUEUED),
    (S.AWAITING_APPROVAL, S.EXPIRED),
    (S.AWAITING_APPROVAL, S.CANCEL_REQUESTED),
    (S.NEEDS_REVIEW, S.AWAITING_APPROVAL),
    (S.NEEDS_REVIEW, S.CANCELLED),
    (S.QUEUED, S.RUNNING),
    (S.QUEUED, S.CANCEL_REQUESTED),
    (S.RUNNING, S.SUCCEEDED),
    (S.RUNNING, S.PARTIAL),
    (S.RUNNING, S.FAILED),
    (S.RUNNING, S.NEEDS_REVIEW),
    (S.RUNNING, S.CANCEL_REQUESTED),
    (S.CANCEL_REQUESTED, S.CANCELLED),
}


def test_there_are_12_states():
    assert len(RunState) == 12


@pytest.mark.parametrize(("source", "target"), list(product(RunState, repeat=2)))
def test_only_listed_pairs_are_allowed(source, target):
    assert can_move(source, target) is ((source, target) in ALLOWED)


@pytest.mark.parametrize(("state", "action"), list(product(RunState, RunAction)))
def test_next_state_follows_the_table_or_raises(state, action):
    if (state, action) in TRANSITIONS:
        assert next_state(state, action) is TRANSITIONS[state, action]
    else:
        with pytest.raises(InvalidTransitionError) as caught:
            next_state(state, action)
        assert caught.value.params == {"from": state.value, "action": action.value}


def test_approve_is_allowed_only_awaiting_approval():
    sources = {state for state, action in TRANSITIONS if action is RunAction.APPROVE}
    assert sources == {S.AWAITING_APPROVAL}
    assert next_state(S.AWAITING_APPROVAL, RunAction.APPROVE) is S.QUEUED


def test_cancel_requests_while_work_may_be_in_flight():
    for state in (S.AWAITING_APPROVAL, S.QUEUED, S.RUNNING):
        assert next_state(state, RunAction.CANCEL) is S.CANCEL_REQUESTED


def test_cancel_in_needs_review_is_immediate():
    assert next_state(S.NEEDS_REVIEW, RunAction.CANCEL) is S.CANCELLED


def test_resolving_a_review_needs_a_new_approval():
    assert next_state(S.NEEDS_REVIEW, RunAction.RESOLVE) is S.AWAITING_APPROVAL


def test_terminal_states_have_no_way_out():
    assert {S.SUCCEEDED, S.PARTIAL, S.FAILED, S.CANCELLED, S.EXPIRED} == TERMINAL_STATES
    assert not {state for state, _ in TRANSITIONS} & TERMINAL_STATES


def test_every_state_is_reachable_from_draft():
    seen, frontier = {S.DRAFT}, [S.DRAFT]
    while frontier:
        state = frontier.pop()
        for (source, _), target in TRANSITIONS.items():
            if source is state and target not in seen:
                seen.add(target)
                frontier.append(target)
    assert seen == set(RunState)


def test_the_table_cannot_be_changed_at_runtime():
    with pytest.raises(TypeError):
        TRANSITIONS[S.SUCCEEDED, RunAction.START] = S.RUNNING  # type: ignore[index]


def test_api_reuses_the_core_enum():
    assert run_models.RunState is RunState
