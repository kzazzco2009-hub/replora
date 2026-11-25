"""Response bodies for §5, the operation registry and limits (docs/api_contract.md)."""

from enum import StrEnum
from typing import Any

from pydantic import Field

from app.api.models import ApiModel


class ArtifactType(StrEnum):
    """The 11 artifact kinds a port can carry (P1.1). Ports match exactly, with no conversion."""

    RAW_FILE = "RawFile"
    ARCHIVE_MANIFEST = "ArchiveManifest"
    TABULAR = "TabularArtifact"
    TEXT_DOCUMENT = "TextDocumentArtifact"
    PAGED = "PagedArtifact"
    PRESENTATION = "PresentationArtifact"
    IMAGE = "ImageArtifact"
    STRUCTURED_OBJECT = "StructuredObjectArtifact"
    VALIDATION_REPORT = "ValidationReport"
    COMPARISON_REPORT = "ComparisonReport"
    OUTPUT_FILE = "OutputFile"


class Port(ApiModel):
    name: str
    artifact_type: ArtifactType
    required: bool


class OperationContract(ApiModel):
    """A known operation. The frontend renders its parameter form from `params_schema`."""

    id: str
    version: int
    title_key: str = Field(description="i18n key for the operation's name")
    inputs: list[Port]
    outputs: list[Port]
    params_schema: dict[str, Any] = Field(
        description=(
            "JSON Schema, limited to the subset in docs/api_contract.md §5: string, integer, "
            "boolean, enum and array of strings; no oneOf, anyOf or $ref"
        )
    )


class Limits(ApiModel):
    """Server limits. The frontend reads them from here and never hard-codes them."""

    max_file_size: int = Field(description="Bytes")
    max_files_per_run: int
    max_nodes: int = Field(description="Most nodes in one workflow")
    workspace_quota: int = Field(description="Bytes of storage per workspace")
