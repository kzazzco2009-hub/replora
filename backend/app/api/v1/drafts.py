"""§6 templates and drafts (docs/api_contract.md): the TemplatePlanner on the workspace's files.

The AI planner (`planner: "ai"`) is Phase 12 and still answers 501.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import StaleDataError

from app.api.problem import (
    ERROR_RESPONSES,
    NOT_FOUND_RESPONSE,
    PRECONDITION_RESPONSES,
    ProblemError,
    invalid,
    not_implemented,
)
from app.api.session import database
from app.api.v1.draft_models import (
    AiDisclosure,
    Draft,
    DraftCreate,
    DraftUpdate,
    Template,
    TemplateInput,
)
from app.api.v1.operations import CACHED_FOR_AN_HOUR
from app.auth.access import not_found
from app.core.draft import WorkflowDraft
from app.core.engine.executor import OperationError
from app.core.plan_hash import plan_hash
from app.core.planner.template import TEMPLATES, plan
from app.core.validation import ValidationReport
from app.core.validator import validate
from app.db import models as m
from app.db.repos import get, scoped
from app.ops.facts import file_facts
from app.ops.registry import REGISTRY


def with_etag(status: int) -> dict[int | str, dict[str, Any]]:
    """Document the `ETag` that every `Draft` response carries; send it back as `If-Match`."""
    etag = {"description": "Send back as `If-Match` on PATCH", "schema": {"type": "string"}}
    return {status: {"headers": {"ETag": etag}}}


templates = APIRouter(tags=["templates"], responses=CACHED_FOR_AN_HOUR)
drafts = APIRouter(
    prefix="/workspaces/{ws_id}/drafts",
    tags=["drafts"],
    responses=ERROR_RESPONSES | NOT_FOUND_RESPONSE,
)


@templates.get("/templates", name="list")
def list_templates() -> list[Template]:
    """The TemplatePlanner's templates (P3.9), for the template picker."""
    return [
        Template(id=spec.id, title_key=spec.title_key, description_key=spec.description_key,
                 required_inputs=[TemplateInput(title_key=f"templates.{spec.id}.inputs.{i}",
                                                artifact_type=kind)
                                  for i, kind in enumerate(spec.required_inputs)])
        for spec in TEMPLATES.values()
    ]  # fmt: skip


@drafts.post("", status_code=201, name="create", responses=with_etag(201))
def create_draft(ws_id: UUID, body: DraftCreate, request: Request, response: Response) -> Draft:
    """Plan a workflow from files and a template or prompt. Validated, not yet approved."""
    if body.planner != "template":
        raise not_implemented()
    if body.template_id not in TEMPLATES:
        raise invalid("body.template_id", "MISSING" if body.template_id is None else "INVALID")
    with database(request).begin() as session:
        files = [_ready_file(session, ws_id, file_id) for file_id in body.file_ids]
        facts = [_facts(request, row, index) for index, row in enumerate(files)]
        try:
            planned = plan(body.template_id, facts)
        except ValueError as error:
            raise invalid("body.file_ids", "INVALID", count=len(files)) from error
        row = m.Draft(workspace_id=ws_id, created_by=request.state.caller.user.id,
                      prompt=body.prompt, draft=planned.model_dump(mode="json"),
                      file_ids=[str(f.id) for f in files], plan_hash=plan_hash(planned.definition),
                      planner="template")  # fmt: skip
        session.add(row)
        session.flush()
        return _answer(session, ws_id, row, response)


@drafts.get("/{draft_id}", name="get", responses=with_etag(200))
def get_draft(ws_id: UUID, draft_id: UUID, request: Request, response: Response) -> Draft:
    """One draft."""
    with database(request)() as session:
        return _answer(session, ws_id, _draft(session, ws_id, draft_id), response)


@drafts.patch("/{draft_id}", name="update", responses=with_etag(200) | PRECONDITION_RESPONSES)
def update_draft(
    ws_id: UUID,
    draft_id: UUID,
    body: DraftUpdate,
    request: Request,
    response: Response,
    if_match: Annotated[
        str | None,
        Header(alias="If-Match", description="The draft's `ETag`. Required: 428 when missing"),
    ] = None,
) -> Draft:
    """Replace the whole definition. It is re-validated and gets a new `plan_hash`.

    The planner's warnings were about its own choices, so the edited draft drops them.
    """
    if if_match is None:
        raise ProblemError(428, "PRECONDITION_REQUIRED", "If-Match is required")
    stale = ProblemError(412, "PRECONDITION_FAILED", "The draft changed; reload it")
    try:
        with database(request).begin() as session:
            row = _draft(session, ws_id, draft_id)
            if _etag(row) != if_match:
                raise stale
            old = WorkflowDraft.model_validate(row.draft)
            edited = WorkflowDraft(definition=body.definition, explanation=old.explanation)
            row.draft, row.plan_hash = edited.model_dump(mode="json"), plan_hash(body.definition)
            flag_modified(row, "draft")  # an unchanged draft still runs the version check
            session.flush()
            return _answer(session, ws_id, row, response)
    except StaleDataError as error:
        raise stale from error


def _etag(row: m.Draft) -> str:
    return f'"{row.plan_hash}"'


def _draft(session: Session, ws_id: UUID, draft_id: UUID) -> m.Draft:
    row = get(session, m.Draft, ws_id, draft_id)
    if row is None:
        raise not_found()
    return row


def _ready_file(session: Session, ws_id: UUID, file_id: UUID) -> m.File:
    row = get(session, m.File, ws_id, file_id)
    if row is None or row.status != "ready":
        raise not_found()
    return row


def _facts(request: Request, row: m.File, index: int):
    if row.detected_type not in ("csv", "json"):
        raise invalid(f"body.file_ids.{index}", "INVALID", detected_type=row.detected_type)
    try:
        content = request.app.state.storage.open(row.storage_key)
        return file_facts(row.display_name, row.detected_type, content)
    except OperationError as error:
        raise invalid(f"body.file_ids.{index}", error.code, **error.params) from error


def checked(session: Session, ws_id: UUID, row: m.Draft) -> tuple[WorkflowDraft, ValidationReport]:
    """The draft and its validation now, against its files, with the planner's warnings."""
    drafted = WorkflowDraft.model_validate(row.draft)
    ids = [UUID(value) for value in row.file_ids]
    sizes = session.scalars(scoped(m.File, ws_id).where(m.File.id.in_(ids))).all()
    report = validate(drafted.definition, REGISTRY, [f.size for f in sizes])
    return drafted, report.model_copy(update={"warnings": [*report.warnings, *drafted.warnings]})


def _answer(session: Session, ws_id: UUID, row: m.Draft, response: Response) -> Draft:
    """The draft as the API shows it, with its `ETag` set."""
    drafted, report = checked(session, ws_id, row)
    response.headers["ETag"] = _etag(row)
    return Draft(id=row.id, prompt=row.prompt, planner=row.planner,
                 definition=drafted.definition, plan_hash=row.plan_hash,
                 explanation=drafted.explanation,
                 ai_disclosure=AiDisclosure(sent_fields=[], samples_sent=False),
                 validation=report, created_at=row.created_at)  # fmt: skip
