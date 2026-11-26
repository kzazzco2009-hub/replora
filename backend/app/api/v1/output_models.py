"""Response bodies for the §7 run outputs (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from app.api.models import ApiModel
from app.api.v1.operation_models import ArtifactType

ReconcileStatus = Literal["matched", "value_diff", "missing_left", "missing_right"]
MAX_SAFE_INTEGER = 2**53 - 1
SafeInt = Annotated[int, Field(ge=-MAX_SAFE_INTEGER, le=MAX_SAFE_INTEGER)]
Cell = str | SafeInt | bool | None
"""Decimals and dates are strings, so no precision is lost (D14).

An `integer` cell fits a JavaScript number exactly; a column with larger values is `decimal`.
"""


class OutputArtifact(ApiModel):
    id: UUID
    name: str
    type: ArtifactType
    format: str = Field(description="File format, for example `csv` or `xlsx`")
    size: int = Field(description="Bytes")
    row_count: int | None = None
    created_at: datetime


class Column(ApiModel):
    name: str
    type: Literal["string", "decimal", "integer", "date", "boolean"]
    nullable: bool


class PreviewRow(ApiModel):
    """One output row; `cells` follow `columns` in order."""

    row: int = Field(ge=0, description="The output row number, as taken by the lineage path")
    status: ReconcileStatus | None = Field(description="Null outside a reconciliation")
    cells: list[Cell]


class Preview(ApiModel):
    """One page of an output table."""

    columns: list[Column]
    rows: list[PreviewRow]
    total: int = Field(description="Rows matching the filter")
    offset: int


class LineageSource(ApiModel):
    """Where an output row came from: a file, the member inside a ZIP, a row, a PDF page."""

    file_id: UUID
    member_path: str | None = None
    row: int
    page: int | None = None


class OperationRef(ApiModel):
    id: str
    version: int


class Lineage(ApiModel):
    sources: list[LineageSource]
    operations: list[OperationRef]
