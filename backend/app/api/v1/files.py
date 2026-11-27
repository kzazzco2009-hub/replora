"""§4 files with direct-to-storage upload (docs/api_contract.md). 501 stubs until Phase 6."""

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.models import Cursor, Limit
from app.api.problem import (
    ERROR_RESPONSES,
    NOT_FOUND_RESPONSE,
    TOO_LARGE_RESPONSE,
    ProblemError,
)
from app.api.session import database, now
from app.api.v1.file_models import (
    DetectedType,
    DownloadLink,
    File,
    FilePage,
    UploadIntent,
    UploadIntentRequest,
    UploadTarget,
)
from app.auth import audit
from app.auth.access import not_found
from app.db import models as m
from app.db.repos import get, page_query, scoped
from app.files import service

SAMPLES = Path(__file__).resolve().parents[2] / "files" / "samples"
"""The onboarding samples: the Phase 7 acceptance files (O-101…O-104)."""

router = APIRouter(
    prefix="/workspaces/{ws_id}/files",
    tags=["files"],
    responses=ERROR_RESPONSES | NOT_FOUND_RESPONSE,
)


@router.post("/upload-intent", status_code=201, responses=TOO_LARGE_RESPONSE)
def create_upload_intent(ws_id: UUID, body: UploadIntentRequest, request: Request) -> UploadIntent:
    """Reserve a file and get the URL to PUT its bytes to. Then call `complete`."""
    if body.size > service.MAX_FILE_SIZE:
        raise ProblemError(413, "FILE_TOO_LARGE", "The file is larger than 50 MiB")
    at, user = now(request), request.state.caller.user
    with database(request).begin() as session:
        row = service.new_file(ws_id, user.id, body.display_name, body.size, at)
        session.add(row)
    target = request.app.state.storage.create_upload_url(row.storage_key, row.size, at)
    upload = UploadTarget(url=target.url, method="PUT", headers=target.headers,
                          expires_at=target.expires_at)  # fmt: skip
    return UploadIntent(file_id=row.id, upload=upload)


@router.post("/{file_id}/complete", name="complete")
def complete_upload(ws_id: UUID, file_id: UUID, request: Request) -> File:
    """Validate the uploaded bytes: `ready`, or `rejected` with a `rejection_code`."""
    with database(request).begin() as session:
        row = _file(session, ws_id, file_id)
        if row.status != "pending":
            raise ProblemError(409, "INVALID_STATE_TRANSITION", "The file is already complete")
        service.complete(row, request.app.state.storage)
        if row.status == "ready":
            audit.record(session, "file.uploaded", request.state.caller.user.id,
                         workspace_id=ws_id, target_type="file", target_id=str(row.id))  # fmt: skip
    return to_file(row)


@router.post("/samples", status_code=201)
def add_samples(ws_id: UUID, request: Request) -> list[File]:
    """Copy the bundled onboarding sample files into the workspace (status `ready`)."""
    storage, at, user = request.app.state.storage, now(request), request.state.caller.user
    rows = []
    with database(request).begin() as session:
        for sample in sorted(SAMPLES.iterdir()):
            data = sample.read_bytes()
            row = service.new_file(ws_id, user.id, sample.name, len(data), at)
            storage.put(row.storage_key, data)
            service.complete(row, storage)
            session.add(row)
            rows.append(row)
    return [to_file(row) for row in rows]


@router.get("", name="list")
def list_files(
    ws_id: UUID,
    request: Request,
    cursor: Cursor = None,
    limit: Limit = 25,
    detected_type: Annotated[DetectedType | None, Query(alias="type")] = None,
) -> FilePage:
    """The workspace files, newest first."""
    with database(request)() as session:
        after = _cursor(session, ws_id, cursor)
        query = scoped(m.File, ws_id)
        if detected_type is not None:
            query = query.where(m.File.detected_type == detected_type)
        rows = page_query(session, query, m.File, limit + 1, after)
    more = len(rows) > limit
    rows = rows[:limit]
    return FilePage(items=[to_file(row) for row in rows],
                    next_cursor=str(rows[-1].id) if more else None)  # fmt: skip


@router.get("/{file_id}", name="get")
def get_file(ws_id: UUID, file_id: UUID, request: Request) -> File:
    """One file."""
    with database(request)() as session:
        return to_file(_file(session, ws_id, file_id))


@router.get("/{file_id}/download", name="download")
def get_download_link(ws_id: UUID, file_id: UUID, request: Request) -> DownloadLink:
    """A short-lived signed download URL."""
    with database(request).begin() as session:
        row = _file(session, ws_id, file_id)
        if row.status != "ready":
            raise ProblemError(409, "INVALID_STATE_TRANSITION", "The file isn't ready")
        audit.record(session, "file.downloaded", request.state.caller.user.id,
                     workspace_id=ws_id, target_type="file", target_id=str(file_id))  # fmt: skip
    url, expires = request.app.state.storage.signed_download_url(
        row.storage_key, row.display_name, now(request)
    )
    return DownloadLink(url=url, expires_at=expires)


@router.delete("/{file_id}", status_code=204, name="delete")
def delete_file(ws_id: UUID, file_id: UUID, request: Request) -> None:
    """Delete the file and its stored bytes."""
    with database(request).begin() as session:
        row = _file(session, ws_id, file_id)
        request.app.state.storage.delete(row.storage_key)
        session.delete(row)
        audit.record(session, "file.deleted", request.state.caller.user.id,
                     workspace_id=ws_id, target_type="file", target_id=str(file_id))  # fmt: skip


def _file(session, ws_id: UUID, file_id: UUID) -> m.File:
    row = get(session, m.File, ws_id, file_id)
    if row is None:
        raise not_found()
    return row


def to_file(row: m.File) -> File:
    return File(id=row.id, display_name=row.display_name, detected_type=row.detected_type,
                size=row.size, sha256=row.sha256, status=row.status,
                rejection_code=row.rejection_code, members=row.members,
                uploaded_by=row.uploaded_by, created_at=row.created_at,
                expires_at=row.expires_at)  # fmt: skip


def _cursor(session, ws_id: UUID, cursor: str | None) -> m.File | None:
    """The row a `next_cursor` points at. A cursor that isn't one of ours is a 422."""
    if cursor is None:
        return None
    try:
        row = get(session, m.File, ws_id, UUID(cursor))
    except ValueError:
        row = None
    if row is None:
        raise ProblemError(422, "VALIDATION_FAILED", "Invalid cursor")
    return row
