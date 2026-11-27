"""§4 files with direct-to-storage upload (docs/api_contract.md). 501 stubs until Phase 6."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.models import Cursor, Limit
from app.api.problem import (
    ERROR_RESPONSES,
    NOT_FOUND_RESPONSE,
    TOO_LARGE_RESPONSE,
    ProblemError,
    not_implemented,
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
from app.db.repos import get
from app.files import service

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
def add_samples(ws_id: UUID) -> list[File]:
    """Copy the bundled onboarding sample files into the workspace (status `ready`)."""
    raise not_implemented()


@router.get("", name="list")
def list_files(
    ws_id: UUID,
    cursor: Cursor = None,
    limit: Limit = 25,
    detected_type: Annotated[DetectedType | None, Query(alias="type")] = None,
) -> FilePage:
    """The workspace files, newest first."""
    raise not_implemented()


@router.get("/{file_id}", name="get")
def get_file(ws_id: UUID, file_id: UUID, request: Request) -> File:
    """One file."""
    with database(request)() as session:
        return to_file(_file(session, ws_id, file_id))


@router.get("/{file_id}/download", name="download")
def get_download_link(ws_id: UUID, file_id: UUID) -> DownloadLink:
    """A short-lived signed download URL."""
    raise not_implemented()


@router.delete("/{file_id}", status_code=204, name="delete")
def delete_file(ws_id: UUID, file_id: UUID) -> None:
    """Delete the file and its stored bytes."""
    raise not_implemented()


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
