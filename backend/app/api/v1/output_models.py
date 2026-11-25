"""Response bodies for the §7 run outputs (docs/api_contract.md)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.api.models import ApiModel
from app.api.v1.operation_models import ArtifactType

ReconcileStatus = Literal["matched", "value_diff", "missing_left", "missing_right"]
Cell = str | int | bool | None
"""Decimals and dates are strings, so no precision is lost (D14)."""


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


class Preview(ApiModel):
    """One page of an output table; `rows` follow `columns` in order."""

    columns: list[Column]
    rows: list[list[Cell]]
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
