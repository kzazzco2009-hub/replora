"""§6 templates and drafts (docs/api_contract.md). 501 stubs until Phase 8."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header

from app.api.problem import (
    ERROR_RESPONSES,
    NOT_FOUND_RESPONSE,
    PRECONDITION_RESPONSES,
    not_implemented,
)
from app.api.v1.draft_models import Draft, DraftCreate, DraftUpdate, Template
from app.api.v1.operations import CACHED_FOR_AN_HOUR


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
    raise not_implemented()


@drafts.post("", status_code=201, name="create", responses=with_etag(201))
def create_draft(ws_id: UUID, body: DraftCreate) -> Draft:
    """Plan a workflow from files and a template or prompt. Validated, not yet approved."""
    raise not_implemented()


@drafts.get("/{draft_id}", name="get", responses=with_etag(200))
def get_draft(ws_id: UUID, draft_id: UUID) -> Draft:
    """One draft."""
    raise not_implemented()


@drafts.patch("/{draft_id}", name="update", responses=with_etag(200) | PRECONDITION_RESPONSES)
def update_draft(
    ws_id: UUID,
    draft_id: UUID,
    body: DraftUpdate,
    if_match: Annotated[
        str | None,
        Header(alias="If-Match", description="The draft's `ETag`. Required: 428 when missing"),
    ] = None,
) -> Draft:
    """Replace the whole definition. It is re-validated and gets a new `plan_hash`."""
    raise not_implemented()
