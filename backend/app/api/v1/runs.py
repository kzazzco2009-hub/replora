"""§7 runs lifecycle (docs/api_contract.md). 501 stubs until Phase 8."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query

from app.api.models import Cursor, Limit
from app.api.problem import ERROR_RESPONSES, NOT_FOUND_RESPONSE, not_implemented
from app.api.v1.run_models import (
    ApproveRequest,
    Run,
    RunEvents,
    RunFromDraft,
    RunFromWorkflow,
    RunState,
    RunSummaryPage,
)

IdempotencyKey = Annotated[
    UUID,
    Header(
        alias="Idempotency-Key",
        description="One per user action, reused on retry. A reuse with another body is 409",
    ),
]

router = APIRouter(
    prefix="/workspaces/{ws_id}/runs",
    tags=["runs"],
    responses=ERROR_RESPONSES | NOT_FOUND_RESPONSE,
)


@router.post("", status_code=201, name="create")
def create_run(
    ws_id: UUID, body: RunFromDraft | RunFromWorkflow, idempotency_key: IdempotencyKey
) -> Run:
    """Start a run from a draft or a saved workflow. It waits in `AWAITING_APPROVAL`.

    A draft that is not valid is refused with 422 `DRAFT_INVALID`, its issues in `errors`.
    """
    raise not_implemented()


@router.post("/{run_id}/approve", status_code=202, name="approve")
def approve_run(
    ws_id: UUID, run_id: UUID, body: ApproveRequest, idempotency_key: IdempotencyKey
) -> Run:
    """Approve the exact plan shown: 409 `PLAN_HASH_MISMATCH` if it changed.

    Only from `AWAITING_APPROVAL`; otherwise 409 `INVALID_STATE_TRANSITION`.
    """
    raise not_implemented()


@router.post("/{run_id}/cancel", status_code=202, name="cancel")
def cancel_run(ws_id: UUID, run_id: UUID) -> Run:
    """Ask to stop. From `AWAITING_APPROVAL`, `QUEUED` or `RUNNING`; else 409."""
    raise not_implemented()


@router.get("", name="list")
def list_runs(
    ws_id: UUID, cursor: Cursor = None, limit: Limit = 25, state: RunState | None = None
) -> RunSummaryPage:
    """The workspace runs, newest first."""
    raise not_implemented()


@router.get("/{run_id}", name="get")
def get_run(ws_id: UUID, run_id: UUID) -> Run:
    """One run with its nodes."""
    raise not_implemented()


@router.get("/{run_id}/events", name="events")
def get_run_events(ws_id: UUID, run_id: UUID, after: Annotated[int, Query(ge=0)] = 0) -> RunEvents:
    """Events after sequence number `after`. Poll every 1 s, backing off to 5 s."""
    raise not_implemented()
