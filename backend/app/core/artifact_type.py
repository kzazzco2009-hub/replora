"""The artifact kinds a port can carry."""

from enum import StrEnum


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
