"""The run lifecycle as data: 12 states and the allowed transitions (P1.5, docs/api_contract.md §7).

`TRANSITIONS` maps `(state, action)` to the next state. A pair it doesn't list is illegal, and the
API answers it with 409 `INVALID_STATE_TRANSITION` and `params: {from, action}`.
"""

from enum import StrEnum
from types import MappingProxyType


class RunState(StrEnum):
    """The 12 run states. The allowed transitions are the P1.5 table, locked at G1."""

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class RunAction(StrEnum):
    """What moves a run: a user action (approve, resolve, cancel) or an engine event."""

    VALIDATE = "validate"
    REQUEST_APPROVAL = "request_approval"
    REQUEST_REVIEW = "request_review"
    RESOLVE = "resolve"
    APPROVE = "approve"
    EXPIRE = "expire"
    START = "start"
    SUCCEED = "succeed"
    FINISH_PARTIAL = "finish_partial"
    FAIL = "fail"
    CANCEL = "cancel"
    CONFIRM_CANCEL = "confirm_cancel"


S, A = RunState, RunAction

TRANSITIONS = MappingProxyType(
    {
        (S.DRAFT, A.VALIDATE): S.VALIDATED,
        (S.VALIDATED, A.REQUEST_APPROVAL): S.AWAITING_APPROVAL,
        (S.VALIDATED, A.REQUEST_REVIEW): S.NEEDS_REVIEW,
        (S.AWAITING_APPROVAL, A.APPROVE): S.QUEUED,
        (S.AWAITING_APPROVAL, A.EXPIRE): S.EXPIRED,
        (S.AWAITING_APPROVAL, A.CANCEL): S.CANCEL_REQUESTED,
        (S.NEEDS_REVIEW, A.RESOLVE): S.AWAITING_APPROVAL,
        (S.NEEDS_REVIEW, A.CANCEL): S.CANCELLED,
        (S.QUEUED, A.START): S.RUNNING,
        (S.QUEUED, A.CANCEL): S.CANCEL_REQUESTED,
        (S.RUNNING, A.SUCCEED): S.SUCCEEDED,
        (S.RUNNING, A.FINISH_PARTIAL): S.PARTIAL,
        (S.RUNNING, A.FAIL): S.FAILED,
        (S.RUNNING, A.REQUEST_REVIEW): S.NEEDS_REVIEW,
        (S.RUNNING, A.CANCEL): S.CANCEL_REQUESTED,
        (S.CANCEL_REQUESTED, A.CONFIRM_CANCEL): S.CANCELLED,
    }
)

TERMINAL_STATES = frozenset(RunState) - {state for state, _ in TRANSITIONS}


class InvalidTransitionError(ValueError):
    """An action the table doesn't allow in the run's current state."""

    def __init__(self, state: RunState, action: RunAction) -> None:
        self.params = {"from": state.value, "action": action.value}
        super().__init__(f"{action.value} is not allowed in {state.value}")


def next_state(state: RunState, action: RunAction) -> RunState:
    """The state `action` leads to, or `InvalidTransitionError`."""
    try:
        return TRANSITIONS[state, action]
    except KeyError:
        raise InvalidTransitionError(state, action) from None


def can_move(source: RunState, target: RunState) -> bool:
    """Whether some action leads from `source` straight to `target`."""
    return any(s is source and t is target for (s, _), t in TRANSITIONS.items())
