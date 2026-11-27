"""A run and how it moves (P3.1), and approval bound to `plan_hash` (P3.2, S-11).

`transition` is the only way a run changes state, and it follows the P1.5 table. Approval goes
through `approve`, which records who approved which hash and when. A run starts only while that
hash still matches its definition, so any change to the plan after approval invalidates it.
"""

from datetime import datetime
from uuid import UUID, uuid7

from app.core.model import ContractModel
from app.core.plan_hash import plan_hash
from app.core.run_state import RunAction, RunState, next_state
from app.core.workflow import WorkflowDefinition


class PlanHashMismatchError(ValueError):
    """The approval doesn't match the plan the run would execute."""

    code = "PLAN_HASH_MISMATCH"


class Approval(ContractModel):
    plan_hash: str
    by: UUID
    at: datetime


class Run(ContractModel):
    id: UUID
    definition: WorkflowDefinition
    state: RunState = RunState.DRAFT
    created_at: datetime
    approval: Approval | None = None

    @property
    def plan_hash(self) -> str:
        return plan_hash(self.definition)


def new_run(definition: WorkflowDefinition, now: datetime) -> Run:
    return Run(id=uuid7(), definition=definition, created_at=now)


def transition(run: Run, action: RunAction) -> Run:
    """The run after `action`, or `InvalidTransitionError`. Starting needs a valid approval."""
    target = next_state(run.state, action)
    if action is RunAction.APPROVE:
        raise ValueError("use approve(), which checks the plan_hash")
    if action is RunAction.START:
        check_approval(run)
    return run.model_copy(update={"state": target})


def approve(run: Run, approved_hash: str, by: UUID, at: datetime) -> Run:
    """Approve the plan the user saw. A different hash is rejected and the run is unchanged."""
    target = next_state(run.state, RunAction.APPROVE)
    if approved_hash != run.plan_hash:
        raise PlanHashMismatchError("the approved plan_hash is not the run's plan")
    approval = Approval(plan_hash=approved_hash, by=by, at=at)
    return run.model_copy(update={"state": target, "approval": approval})


def check_approval(run: Run) -> None:
    """Raise unless the run has an approval for exactly its current plan."""
    if run.approval is None or run.approval.plan_hash != run.plan_hash:
        raise PlanHashMismatchError("the run has no approval for its current plan")
