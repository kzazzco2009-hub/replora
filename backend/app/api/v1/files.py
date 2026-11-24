"""§4 files with direct-to-storage upload (docs/api_contract.md). 501 stubs until Phase 6."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.models import Cursor, Limit
from app.api.problem import (
    ERROR_RESPONSES,
    NOT_FOUND_RESPONSE,
    TOO_LARGE_RESPONSE,
    not_implemented,
)
from app.api.v1.file_models import (
    DetectedType,
    DownloadLink,
    File,
    FilePage,
    UploadIntent,
    UploadIntentRequest,
)

router = APIRouter(
    prefix="/workspaces/{ws_id}/files",
    tags=["files"],
    responses=ERROR_RESPONSES | NOT_FOUND_RESPONSE,
)


@router.post("/upload-intent", status_code=201, responses=TOO_LARGE_RESPONSE)
def create_upload_intent(ws_id: UUID, body: UploadIntentRequest) -> UploadIntent:
    """Reserve a file and get the URL to PUT its bytes to. Then call `complete`."""
    raise not_implemented()


@router.post("/{file_id}/complete", name="complete")
def complete_upload(ws_id: UUID, file_id: UUID) -> File:
    """Validate the uploaded bytes: `ready`, or `rejected` with a `rejection_code`."""
    raise not_implemented()


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
def get_file(ws_id: UUID, file_id: UUID) -> File:
    """One file."""
    raise not_implemented()


@router.get("/{file_id}/download", name="download")
def get_download_link(ws_id: UUID, file_id: UUID) -> DownloadLink:
    """A short-lived signed download URL."""
    raise not_implemented()


@router.delete("/{file_id}", status_code=204, name="delete")
def delete_file(ws_id: UUID, file_id: UUID) -> None:
    """Delete the file and its stored bytes."""
    raise not_implemented()
