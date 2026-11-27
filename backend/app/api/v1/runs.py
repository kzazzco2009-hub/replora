"""§7 runs lifecycle (docs/api_contract.md): create, approve, cancel, read and poll (P8.1, P8.4).

Approving or cancelling hands the run to the worker with a `run_step` job (P8.2). A run from a
saved workflow (Phase 13) and `resolve` still answer 501.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.models import Cursor, Limit
from app.api.problem import (
    ERROR_RESPONSES,
    NOT_FOUND_RESPONSE,
    ProblemError,
    ProblemItem,
    invalid,
    not_implemented,
)
from app.api.session import database, now
from app.api.v1 import run_models as api
from app.api.v1.drafts import checked
from app.api.v1.run_models import (
    ApproveRequest,
    ResolveRequest,
    RunEvents,
    RunFromDraft,
    RunFromWorkflow,
    RunState,
    RunSummaryPage,
)
from app.auth import audit
from app.auth.access import not_found
from app.core.engine.run import (
    PlanHashMismatchError,
    approval_expires_at,
    approve,
    expire_if_stale,
    new_run,
    transition,
)
from app.core.engine.run import Run as EngineRun
from app.core.run_state import InvalidTransitionError, RunAction
from app.db import models as m
from app.db.engine_state import apply, load_run
from app.db.jobs import enqueue
from app.db.repos import get, page_query, scoped
from app.db.run_events import emit

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
MISMATCH = ProblemError(409, "IDEMPOTENCY_KEY_MISMATCH", "The key was used for another request")


@router.post("", status_code=201, name="create")
def create_run(
    ws_id: UUID, body: RunFromDraft | RunFromWorkflow, idempotency_key: IdempotencyKey,
    request: Request,
) -> api.Run:  # fmt: skip
    """Start a run from a draft or a saved workflow. It waits in `AWAITING_APPROVAL`.

    A draft that is not valid is refused with 422 `DRAFT_INVALID`, its issues in `errors`.
    """
    if isinstance(body, RunFromWorkflow):
        raise not_implemented()
    try:
        with database(request).begin() as session:
            return _create(session, ws_id, body, str(idempotency_key), request)
    except IntegrityError:
        with database(request)() as session:  # the same key won a race: answer with its run
            return _created(session, ws_id, body, str(idempotency_key), request)


def _created(session: Session, ws_id: UUID, body: RunFromDraft, key: str, request: Request):
    row = session.scalars(scoped(m.Run, ws_id).where(m.Run.idempotency_key == key)).one()
    if row.draft_id != body.draft_id:
        raise MISMATCH
    return to_run(session, ws_id, row, request)


def _create(session: Session, ws_id: UUID, body: RunFromDraft, key: str, request: Request):
    if session.scalars(scoped(m.Run, ws_id).where(m.Run.idempotency_key == key)).first():
        return _created(session, ws_id, body, key, request)
    draft = get(session, m.Draft, ws_id, body.draft_id)
    if draft is None:
        raise not_found()
    drafted, report = checked(session, ws_id, draft)
    if not report.valid:
        items = [ProblemItem(path=i.path, code=i.code, params=i.params) for i in report.errors]
        raise ProblemError(422, "DRAFT_INVALID", "The draft is not valid", errors=items)
    at, user = now(request), request.state.caller.user
    run = new_run(drafted.definition, at)
    run = transition(transition(run, RunAction.VALIDATE, at), RunAction.REQUEST_APPROVAL, at)
    row = m.Run(id=run.id, workspace_id=ws_id, draft_id=draft.id, plan_hash=run.plan_hash,
                idempotency_key=key, file_ids=draft.file_ids, created_at=at,
                definition=run.definition.model_dump(mode="json"))  # fmt: skip
    apply(row, run)
    session.add(row)
    session.flush()
    emit(session, row.id, "state_changed", at, state=row.state)
    audit.record(session, "run.created", user.id, workspace_id=ws_id, target_type="run",
                 target_id=str(row.id))  # fmt: skip
    return to_run(session, ws_id, row, request)


@router.post("/{run_id}/approve", status_code=202, name="approve")
def approve_run(
    ws_id: UUID, run_id: UUID, body: ApproveRequest, idempotency_key: IdempotencyKey,
    request: Request,
) -> api.Run:  # fmt: skip
    """Approve the exact plan shown: 409 `PLAN_HASH_MISMATCH` if it changed.

    Only from `AWAITING_APPROVAL`; otherwise 409 `INVALID_STATE_TRANSITION`.
    """
    at, user, key = now(request), request.state.caller.user, str(idempotency_key)
    with database(request).begin() as session:
        row = _run(session, ws_id, run_id)
        if row.approve_key == key:
            if body.plan_hash != row.plan_hash:
                raise MISMATCH
            return to_run(session, ws_id, row, request)
        run = expire_if_stale(load_run(session, ws_id, run_id), at, _ttl(request))
        run = _move(lambda: approve(run, body.plan_hash, user.id, at))
        apply(row, run)
        row.approve_key = key
        _hand_over(session, row, at)
        audit.record(session, "run.approved", user.id, workspace_id=ws_id, target_type="run",
                     target_id=str(row.id))  # fmt: skip
        return to_run(session, ws_id, row, request)


@router.post("/{run_id}/resolve", name="resolve")
def resolve_run(
    ws_id: UUID, run_id: UUID, body: ResolveRequest, idempotency_key: IdempotencyKey
) -> api.Run:
    """Answer the review questions: a new `plan_hash`, waiting again in `AWAITING_APPROVAL`.

    Only from `NEEDS_REVIEW`; otherwise 409 `INVALID_STATE_TRANSITION`.
    409 `PLAN_HASH_MISMATCH` if the plan changed since it was reviewed.
    """
    raise not_implemented()


@router.post("/{run_id}/cancel", status_code=202, name="cancel")
def cancel_run(ws_id: UUID, run_id: UUID, request: Request) -> api.Run:
    """Ask to stop (`AWAITING_APPROVAL`, `QUEUED`, `RUNNING`); `NEEDS_REVIEW` stops at once."""
    at, user = now(request), request.state.caller.user
    with database(request).begin() as session:
        row = _run(session, ws_id, run_id)
        run = load_run(session, ws_id, run_id)
        run = _move(lambda: transition(run, RunAction.CANCEL, at))
        apply(row, run)
        if run.state is RunState.CANCEL_REQUESTED:
            _hand_over(session, row, at)
        else:
            emit(session, row.id, "state_changed", at, state=row.state)
        audit.record(session, "run.cancelled", user.id, workspace_id=ws_id, target_type="run",
                     target_id=str(row.id))  # fmt: skip
        return to_run(session, ws_id, row, request)


@router.get("", name="list")
def list_runs(
    ws_id: UUID, request: Request, cursor: Cursor = None, limit: Limit = 25,
    state: RunState | None = None,
) -> RunSummaryPage:  # fmt: skip
    """The workspace runs, newest first."""
    with database(request)() as session:
        after = None
        if cursor is not None:
            after = _cursor_run(session, ws_id, cursor)
        query = scoped(m.Run, ws_id)
        if state is not None:
            query = query.where(m.Run.state == state.value)
        rows = page_query(session, query, m.Run, limit + 1, after)
        items = [_summary(session, ws_id, row) for row in rows[:limit]]
    return RunSummaryPage(items=items, next_cursor=str(rows[limit - 1].id)
                          if len(rows) > limit else None)  # fmt: skip


@router.get("/{run_id}", name="get")
def get_run(ws_id: UUID, run_id: UUID, request: Request) -> api.Run:
    """One run with its nodes."""
    with database(request)() as session:
        return to_run(session, ws_id, _run(session, ws_id, run_id), request)


@router.get("/{run_id}/events", name="events")
def get_run_events(
    ws_id: UUID, run_id: UUID, request: Request, after: Annotated[int, Query(ge=0)] = 0
) -> RunEvents:
    """Events after sequence number `after`. Poll every 1 s, backing off to 5 s."""
    with database(request)() as session:
        _run(session, ws_id, run_id)
        query = scoped(m.RunEvent, ws_id).where(m.RunEvent.run_id == run_id,
                                                 m.RunEvent.seq > after)  # fmt: skip
        rows = session.scalars(query.order_by(m.RunEvent.seq)).all()
    events = [api.RunEvent(seq=e.seq, type=e.type, node_id=e.node_id, payload=e.payload,
                           created_at=e.created_at) for e in rows]  # fmt: skip
    return RunEvents(events=events, last_seq=rows[-1].seq if rows else after)


def _move(change) -> EngineRun:
    """Apply an engine transition, answering its refusal as the contract's 409."""
    try:
        return change()
    except PlanHashMismatchError as error:
        raise ProblemError(409, "PLAN_HASH_MISMATCH", "The plan changed; review it") from error
    except InvalidTransitionError as error:
        item = ProblemItem(path="state", code="INVALID_STATE_TRANSITION", params=error.params)
        raise ProblemError(409, "INVALID_STATE_TRANSITION", "Not allowed in this state",
                           errors=[item]) from error  # fmt: skip


def _hand_over(session: Session, row: m.Run, at) -> None:
    """Record the new state and give the run to the worker."""
    emit(session, row.id, "state_changed", at, state=row.state)
    enqueue(session, "run_step", {"workspace_id": str(row.workspace_id), "run_id": str(row.id)},
            at)  # fmt: skip


def _ttl(request: Request):
    return request.app.state.settings.approval_ttl


def _run(session: Session, ws_id: UUID, run_id: UUID) -> m.Run:
    row = get(session, m.Run, ws_id, run_id)
    if row is None:
        raise not_found()
    return row


def _cursor_run(session: Session, ws_id: UUID, cursor: str) -> m.Run:
    try:
        row = get(session, m.Run, ws_id, UUID(cursor))
    except ValueError:
        row = None
    if row is None:
        raise invalid("query.cursor", "INVALID")
    return row


def _title(run: EngineRun) -> str:
    """The run's input files, for the list: `orders.csv · payments.json`."""
    return " · ".join(i.label or i.name for i in run.definition.inputs)


def _summary(session: Session, ws_id: UUID, row: m.Run) -> api.RunSummary:
    run = load_run(session, ws_id, row.id)
    return api.RunSummary(id=row.id, state=row.state, title=_title(run),
                          created_at=row.created_at, finished_at=row.finished_at)  # fmt: skip


def to_run(session: Session, ws_id: UUID, row: m.Run, request: Request) -> api.Run:
    """The run as the API shows it, with its nodes."""
    run = load_run(session, ws_id, row.id)
    operations = {node.id: node.operation.id for node in run.definition.nodes}
    nodes = session.scalars(scoped(m.RunNode, ws_id).where(m.RunNode.run_id == row.id)).all()
    return api.Run(
        id=row.id, state=row.state, plan_hash=row.plan_hash, definition=run.definition,
        nodes=[api.RunNode(node_id=n.node_id, operation_id=operations[n.node_id], state=n.state,
                           attempt=n.attempt, started_at=n.started_at, finished_at=n.finished_at,
                           error_code=n.error_code, warnings=n.warnings) for n in nodes],
        approved_by=row.approved_by, approved_at=row.approved_at,
        approval_expires_at=approval_expires_at(run, _ttl(request)),
        created_at=row.created_at, finished_at=row.finished_at,
        review_issues=row.issues if row.state == RunState.NEEDS_REVIEW else [],
    )  # fmt: skip
