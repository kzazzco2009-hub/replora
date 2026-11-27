"""Request and response bodies for §4 files (docs/api_contract.md)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from app.api.models import ApiModel, Page

DetectedType = Literal["csv", "json", "zip"]
"""From magic bytes, never the extension. Phases 14–16 add values (backend_plan.md)."""

RejectionCode = Literal[
    "FILE_EMPTY",
    "FILE_SIZE_MISMATCH",
    "FILE_TYPE_UNSUPPORTED",
    "FILE_CORRUPT",
    "ZIP_ENCRYPTED",
    "ZIP_TOO_MANY_MEMBERS",
    "ZIP_TOO_LARGE",
    "ZIP_RATIO_EXCEEDED",
    "ZIP_NESTED",
    "ZIP_UNSAFE_PATH",
    "ZIP_SYMLINK",
    "ZIP_MEMBER_UNSUPPORTED",
]
"""Why `complete` rejected a file (P6.1–P6.4, S-32). Listed in contracts/error-codes.json."""


class FileMember(ApiModel):
    """A file inside an uploaded ZIP."""

    path: str
    detected_type: DetectedType
    size: int


class File(ApiModel):
    id: UUID
    display_name: str
    detected_type: DetectedType | None = Field(description="Set on `complete`")
    size: int
    sha256: str | None = Field(description="Computed by the server on `complete`")
    status: Literal["pending", "ready", "rejected"]
    rejection_code: RejectionCode | None = None
    members: list[FileMember] | None = None
    uploaded_by: UUID
    created_at: datetime
    expires_at: datetime


class FilePage(Page[File]):
    pass


class UploadIntentRequest(ApiModel):
    display_name: Annotated[str, Field(min_length=1, max_length=255)]
    size: Annotated[int, Field(gt=0, description="Must match the stored size")]
    content_type: str


class UploadTarget(ApiModel):
    """Use exactly as returned. Never build storage URLs on the client."""

    url: str
    method: Literal["PUT"]
    headers: dict[str, str]
    expires_at: datetime


class UploadIntent(ApiModel):
    file_id: UUID
    upload: UploadTarget


class DownloadLink(ApiModel):
    url: str
    expires_at: datetime
