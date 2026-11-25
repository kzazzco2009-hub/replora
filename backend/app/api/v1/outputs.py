"""§7 run outputs: list, preview, download and row lineage (docs/api_contract.md). 501 stubs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query

from app.api.models import Limit
from app.api.problem import ERROR_RESPONSES, NOT_FOUND_RESPONSE, not_implemented
from app.api.v1.file_models import DownloadLink
from app.api.v1.output_models import Lineage, OutputArtifact, Preview, ReconcileStatus

router = APIRouter(
    prefix="/workspaces/{ws_id}/runs/{run_id}/outputs",
    tags=["outputs"],
    responses=ERROR_RESPONSES | NOT_FOUND_RESPONSE,
)


@router.get("", name="list")
def list_outputs(ws_id: UUID, run_id: UUID) -> list[OutputArtifact]:
    """The files a run produced."""
    raise not_implemented()


@router.get("/{artifact_id}/preview", name="preview")
def preview_output(
    ws_id: UUID,
    run_id: UUID,
    artifact_id: UUID,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Limit = 100,
    status: ReconcileStatus | None = None,
    q: Annotated[str | None, Query(max_length=200, description="Text search in cells")] = None,
) -> Preview:
    """A page of an output table, optionally filtered by reconciliation status or text."""
    raise not_implemented()


@router.get("/{artifact_id}/download", name="download")
def download_output(ws_id: UUID, run_id: UUID, artifact_id: UUID) -> DownloadLink:
    """A short-lived signed download URL."""
    raise not_implemented()


@router.get("/{artifact_id}/rows/{row}/lineage", name="lineage")
def get_row_lineage(
    ws_id: UUID, run_id: UUID, artifact_id: UUID, row: Annotated[int, Path(ge=0)]
) -> Lineage:
    """The source rows and operations behind one output row."""
    raise not_implemented()
