"""§7 run outputs (docs/api_contract.md): list, preview, download and row lineage (P8.1).

A run's outputs are its definition's output contracts. Each points at a node's output port, and
`run_nodes.outputs` holds the artifact that port produced.
"""

import csv
import io
import json
from typing import Annotated, get_args
from uuid import UUID

from fastapi import APIRouter, Path, Query, Request
from sqlalchemy.orm import Session

from app.api.models import Limit
from app.api.problem import ERROR_RESPONSES, NOT_FOUND_RESPONSE, invalid
from app.api.session import database, now
from app.api.v1.file_models import DownloadLink
from app.api.v1.output_models import (
    Column,
    Lineage,
    LineageSource,
    OutputArtifact,
    Preview,
    PreviewRow,
    ReconcileStatus,
)
from app.api.v1.run_models import RunCounts
from app.auth import audit
from app.auth.access import not_found
from app.core.artifact_type import ArtifactType
from app.core.operations import OperationRef
from app.db import models as m
from app.db.engine_state import load_run
from app.db.repos import get, scoped

router = APIRouter(
    prefix="/workspaces/{ws_id}/runs/{run_id}/outputs",
    tags=["outputs"],
    responses=ERROR_RESPONSES | NOT_FOUND_RESPONSE,
)


def produced(session: Session, ws_id: UUID, run_id: UUID) -> dict[tuple[str, str], m.Artifact]:
    """Every artifact the run's nodes made, by `(node_id, port)`. 404 when the run isn't here."""
    if get(session, m.Run, ws_id, run_id) is None:
        raise not_found()
    nodes = session.scalars(scoped(m.RunNode, ws_id).where(m.RunNode.run_id == run_id)).all()
    ids = {(n.node_id, port): UUID(ref["id"]) for n in nodes for port, ref in n.outputs.items()}
    rows = session.scalars(scoped(m.Artifact, ws_id).where(m.Artifact.id.in_(ids.values())))
    by_id = {row.id: row for row in rows}
    return {slot: by_id[artifact_id] for slot, artifact_id in ids.items()}


def outputs(session: Session, ws_id: UUID, run_id: UUID) -> dict[str, m.Artifact]:
    """The run's output files by download name, for example `comparison_report.csv`."""
    made = produced(session, ws_id, run_id)
    definition = load_run(session, ws_id, run_id).definition
    return {f"{out.name}.{made[slot].format}": made[slot] for out in definition.outputs
            if (slot := (out.source.node_id, out.source.port)) in made}  # fmt: skip


def summary(session: Session, ws_id: UUID, run_id: UUID, storage) -> RunCounts | None:
    """The reconciliation counts, once the run's `compare` node has made its report."""
    definition = load_run(session, ws_id, run_id).definition
    made = produced(session, ws_id, run_id)
    for node in definition.nodes:
        if node.operation.id == "compare" and (node.id, "report") in made:
            report = json.loads(storage.open(made[node.id, "report"].storage_key))
            return RunCounts(**report["summary"])
    return None


@router.get("", name="list")
def list_outputs(ws_id: UUID, run_id: UUID, request: Request) -> list[OutputArtifact]:
    """The files a run produced."""
    with database(request)() as session:
        return [OutputArtifact(id=row.id, name=name, type=row.type, format=row.format,
                               size=row.size, created_at=row.created_at)
                for name, row in outputs(session, ws_id, run_id).items()]  # fmt: skip


@router.get("/{artifact_id}/preview", name="preview")
def preview_output(
    ws_id: UUID,
    run_id: UUID,
    artifact_id: UUID,
    request: Request,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Limit = 100,
    status: ReconcileStatus | None = None,
    q: Annotated[str | None, Query(max_length=200, description="Text search in cells")] = None,
) -> Preview:
    """A page of an output table, optionally filtered by reconciliation status or text.

    `row` is the row's place in the file (0 is the first row after the header). Cells are text,
    exactly as in the file (formula cells keep their S-37 `'`).
    """
    with database(request)() as session:
        _, row = output(session, ws_id, run_id, artifact_id)
    if row.format != "csv":
        raise invalid("path.artifact_id", "INVALID", format=row.format)
    header, *lines = csv.reader(io.StringIO(request.app.state.storage.open(row.storage_key)
                                            .decode("utf-8-sig")))  # fmt: skip
    marks = [_status(header, line) for line in lines]
    needle = (q or "").casefold()
    found = [(n, line) for n, line in enumerate(lines)
             if (status is None or marks[n] == status)
             and any(needle in cell.casefold() for cell in line)]  # fmt: skip
    return Preview(columns=[Column(name=name, type="string", nullable=True) for name in header],
                   rows=[PreviewRow(row=n, status=marks[n], cells=line)
                         for n, line in found[offset:offset + limit]],
                   total=len(found), offset=offset)  # fmt: skip


def _status(header: list[str], line: list[str]) -> str | None:
    """The reconciliation status of a report row; None in a file without a `status` column."""
    if "status" not in header:
        return None
    value = line[header.index("status")]
    return value if value in get_args(ReconcileStatus) else None


@router.get("/{artifact_id}/download", name="download")
def download_output(ws_id: UUID, run_id: UUID, artifact_id: UUID, request: Request) -> DownloadLink:
    """A short-lived signed download URL."""
    with database(request).begin() as session:
        name, row = output(session, ws_id, run_id, artifact_id)
        user = request.state.caller.user
        audit.record(session, "output.downloaded", user.id, workspace_id=ws_id,
                     target_type="output", target_id=str(artifact_id))  # fmt: skip
    url, expires = request.app.state.storage.signed_download_url(
        row.storage_key, name, now(request)
    )
    return DownloadLink(url=url, expires_at=expires)


def output(session: Session, ws_id: UUID, run_id: UUID, artifact_id: UUID):
    """One of the run's output files with its name; any other artifact is a 404."""
    for name, row in outputs(session, ws_id, run_id).items():
        if row.id == artifact_id:
            return name, row
    raise not_found()


@router.get("/{artifact_id}/rows/{row}/lineage", name="lineage")
def get_row_lineage(
    ws_id: UUID, run_id: UUID, artifact_id: UUID, row: Annotated[int, Path(ge=0)],
    request: Request,
) -> Lineage:  # fmt: skip
    """The source rows and operations behind one output row (P7.4).

    A reconciliation report row has a source on each side it was found on. An output without
    row lineage (one not made from a comparison report), or a row past its end, is a 404.
    """
    with database(request)() as session:
        _, made = output(session, ws_id, run_id, artifact_id)
        parents = [get(session, m.Artifact, ws_id, UUID(p)) for p in made.lineage["parents"]]
    reports = [p for p in parents if p.type == ArtifactType.COMPARISON_REPORT]
    if not reports:
        raise not_found()
    rows = json.loads(request.app.state.storage.open(reports[0].storage_key))["rows"]
    if row >= len(rows):
        raise not_found()
    sides = [s for s in (rows[row]["left_source"], rows[row]["right_source"]) if s]
    ops = dict.fromkeys(op for side in sides for op in side.get("ops", []))
    return Lineage(
        sources=[LineageSource(file_id=s["file_id"], member_path=s.get("member"), row=s["row"])
                 for s in sides],
        operations=[OperationRef(id=op.split("@")[0], version=int(op.split("@")[1]))
                    for op in ops],
    )  # fmt: skip
