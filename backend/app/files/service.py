"""The upload flow (P6.2, P6.3): intent → PUT to storage → complete.

`complete` reads the stored bytes once: it checks the declared size, computes the SHA-256 on the
server (a client hash is never trusted, S-34), and detects the type from the content (S-30).
A rejected file's bytes are deleted; its row stays with the `rejection_code` for the user.
"""

import hashlib
from datetime import datetime, timedelta
from uuid import UUID, uuid7

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.problem import ProblemError
from app.db import models as m
from app.files.detect import detect, safe_display_name
from app.files.zip_safety import inspect

MAX_FILE_SIZE = 50 * 1024 * 1024
INPUT_RETENTION = timedelta(days=30)
"""D11: inputs are kept 30 days."""


def new_file(workspace_id: UUID, user_id: UUID, name: str, size: int, now: datetime) -> m.File:
    file_id = uuid7()
    return m.File(id=file_id, workspace_id=workspace_id, uploaded_by=user_id,
                  storage_key=f"{workspace_id}/{file_id}", display_name=safe_display_name(name),
                  size=size, status="pending", expires_at=now + INPUT_RETENTION)  # fmt: skip


def complete(row: m.File, storage) -> None:
    """Set the file `ready` (with its type and hash) or `rejected` (with the reason)."""
    data = storage.open(row.storage_key) if storage.exists(row.storage_key) else b""
    if not data:
        verdict = "FILE_EMPTY"
    elif len(data) != row.size:
        verdict = "FILE_SIZE_MISMATCH"
    else:
        verdict = detect(data)
    members = inspect(data) if verdict == "zip" else None
    if isinstance(members, str):
        verdict = members
    if verdict.isupper():
        row.status, row.rejection_code = "rejected", verdict
        storage.delete(row.storage_key)
        return
    row.status, row.detected_type, row.members = "ready", verdict, members
    row.sha256 = hashlib.sha256(data).hexdigest()


MAX_FILES_PER_RUN = 10


def check_files_per_run(count: int) -> None:
    """P6.7: a run reads at most 10 files (the runs endpoint calls this, P8.1)."""
    if count > MAX_FILES_PER_RUN:
        raise ProblemError(413, "QUOTA_EXCEEDED", "At most 10 files per run")


def check_quota(session: Session, workspace_id: UUID, size: int, quota: int) -> None:
    """P6.7: the workspace's stored and pending bytes, plus this file, stay within the quota."""
    used = session.scalar(select(func.coalesce(func.sum(m.File.size), 0)).where(
        m.File.workspace_id == workspace_id, m.File.status != "rejected"))  # fmt: skip
    if used + size > quota:
        raise ProblemError(413, "QUOTA_EXCEEDED", "The workspace storage is full")


def purge_expired(session: Session, storage, now: datetime) -> int:
    """P6.6: delete files past `expires_at`, from storage and the database. The count."""
    rows = session.scalars(select(m.File).where(m.File.expires_at <= now)).all()
    for row in rows:
        storage.delete(row.storage_key)
        session.delete(row)
    return len(rows)
