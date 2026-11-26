"""P3.1 `transition` enforces the P1.5 table; P3.2 approval is bound to `plan_hash` (T3.1, S-11)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from validator_samples import node, reconcile_workflow

from app.core.engine.run import (
    Approval,
    PlanHashMismatchError,
    Run,
    approve,
    check_approval,
    new_run,
    transition,
)
from app.core.plan_hash import plan_hash
from app.core.run_state import TRANSITIONS, InvalidTransitionError, RunAction, RunState

USER = uuid4()
NOW = datetime(2026, 11, 26, 12, tzinfo=UTC)


def awaiting() -> Run:
    run = new_run(reconcile_workflow(), NOW)
    run = transition(run, RunAction.VALIDATE)
    return transition(run, RunAction.REQUEST_APPROVAL)


def test_a_new_run_is_a_draft_bound_to_its_plan_hash():
    run = new_run(reconcile_workflow(), NOW)
    assert (run.state, run.approval, run.created_at) == (RunState.DRAFT, None, NOW)
    assert run.plan_hash == plan_hash(reconcile_workflow())


@pytest.mark.parametrize(("pair", "target"), TRANSITIONS.items())
def test_every_allowed_transition_moves_the_run(pair, target):
    state, action = pair
    run = new_run(reconcile_workflow(), NOW)
    signed = Approval(plan_hash=run.plan_hash, by=USER, at=NOW)
    run = run.model_copy(update={"state": state, "approval": signed})
    if action is RunAction.APPROVE:
        assert approve(run, run.plan_hash, USER, NOW).state is target
    else:
        assert transition(run, action).state is target


ILLEGAL = [(s, a) for s in RunState for a in RunAction if (s, a) not in TRANSITIONS]


@pytest.mark.parametrize(("state", "action"), ILLEGAL)
def test_an_illegal_transition_raises_and_changes_nothing(state, action):
    run = new_run(reconcile_workflow(), NOW).model_copy(update={"state": state})
    with pytest.raises(InvalidTransitionError) as caught:
        transition(run, action)
    assert caught.value.params == {"from": state.value, "action": action.value}
    assert run.state is state


def test_approve_is_not_a_plain_transition():
    with pytest.raises(ValueError, match="approve"):
        transition(awaiting(), RunAction.APPROVE)


def test_approval_with_the_right_hash_queues_the_run_and_records_who_and_when():
    run = awaiting()
    approved = approve(run, run.plan_hash, USER, NOW)
    assert approved.state is RunState.QUEUED
    assert (approved.approval.plan_hash, approved.approval.by, approved.approval.at) == (
        run.plan_hash,
        USER,
        NOW,
    )
    check_approval(approved)


def test_approval_with_a_wrong_hash_is_rejected():
    run = awaiting()
    with pytest.raises(PlanHashMismatchError) as caught:
        approve(run, "0" * 64, USER, NOW)
    assert caught.value.code == "PLAN_HASH_MISMATCH"
    assert run.state is RunState.AWAITING_APPROVAL


def test_approval_outside_awaiting_approval_is_an_illegal_transition():
    run = new_run(reconcile_workflow(), NOW)
    with pytest.raises(InvalidTransitionError):
        approve(run, run.plan_hash, USER, NOW)


def test_changing_the_plan_after_approval_invalidates_the_approval():
    approved = approve(awaiting(), awaiting().plan_hash, USER, NOW)
    defn = approved.definition
    changed = defn.model_copy(update={"nodes": [*defn.nodes[:2], node("compare", "reconcile")]})
    tampered = approved.model_copy(update={"definition": changed})
    with pytest.raises(PlanHashMismatchError):
        check_approval(tampered)
    with pytest.raises(PlanHashMismatchError):
        transition(tampered, RunAction.START)


def test_a_run_can_start_only_with_a_valid_approval():
    unapproved = awaiting().model_copy(update={"state": RunState.QUEUED})
    with pytest.raises(PlanHashMismatchError):
        transition(unapproved, RunAction.START)
    approved = approve(awaiting(), awaiting().plan_hash, USER, NOW)
    assert transition(approved, RunAction.START).state is RunState.RUNNING
