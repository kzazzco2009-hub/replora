"""Files, artifacts, workflows, drafts, runs and jobs (P4.2), indexed as `plan.md` §6 lists."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedMixin, IdMixin, JsonDocument

Json = dict[str, Any]


def _workspace() -> Mapped[UUID]:
    return mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))


def _user_or_null() -> Mapped[UUID | None]:
    return mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class File(IdMixin, CreatedMixin, Base):
    __tablename__ = "files"
    __table_args__ = (
        Index("ix_files_ws_created", "workspace_id", "created_at"),
        Index("ix_files_ws_sha256", "workspace_id", "sha256"),
        Index("ix_files_expires_at", "expires_at"),
        Index("ix_files_uploaded_by", "uploaded_by"),
    )

    workspace_id: Mapped[UUID] = _workspace()
    uploaded_by: Mapped[UUID | None] = _user_or_null()
    storage_key: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(255))
    detected_type: Mapped[str | None] = mapped_column(String(32))
    size: Mapped[int]
    sha256: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    rejection_code: Mapped[str | None] = mapped_column(String(32))
    members: Mapped[list[Json] | None] = mapped_column(JsonDocument)
    """For a ZIP: `[{path, detected_type, size}]` (P6.4)."""
    expires_at: Mapped[datetime | None]


class Workflow(IdMixin, CreatedMixin, Base):
    __tablename__ = "workflows"
    __table_args__ = (
        Index("ix_workflows_ws_created", "workspace_id", "created_at"),
        Index("ix_workflows_ws_name", "workspace_id", "name"),
        Index("ix_workflows_created_by", "created_by"),
    )

    workspace_id: Mapped[UUID] = _workspace()
    name: Mapped[str] = mapped_column(String(100))
    created_by: Mapped[UUID | None] = _user_or_null()
    latest_version: Mapped[int] = mapped_column(default=0)
    deleted_at: Mapped[datetime | None]


class WorkflowVersion(IdMixin, CreatedMixin, Base):
    """An immutable, pinned definition (§8)."""

    __tablename__ = "workflow_versions"
    __table_args__ = (
        Index("uq_wfv_workflow_version", "workflow_id", "version", unique=True),
        Index("ix_wfv_plan_hash", "plan_hash"),
    )

    workflow_id: Mapped[UUID] = mapped_column(ForeignKey("workflows.id", ondelete="CASCADE"))
    version: Mapped[int]
    definition: Mapped[Json] = mapped_column(JsonDocument)
    plan_hash: Mapped[str] = mapped_column(String(64))


class Draft(IdMixin, CreatedMixin, Base):
    __tablename__ = "drafts"
    __table_args__ = (
        Index("ix_drafts_ws_created", "workspace_id", "created_at"),
        Index("ix_drafts_created_by", "created_by"),
    )

    workspace_id: Mapped[UUID] = _workspace()
    created_by: Mapped[UUID | None] = _user_or_null()
    prompt: Mapped[str] = mapped_column(Text, default="")
    draft: Mapped[Json] = mapped_column(JsonDocument)
    plan_hash: Mapped[str] = mapped_column(String(64))
    planner: Mapped[str] = mapped_column(String(16))


class Run(IdMixin, CreatedMixin, Base):
    __tablename__ = "runs"
    __table_args__ = (
        Index("ix_runs_ws_created", "workspace_id", "created_at"),
        Index("ix_runs_ws_state", "workspace_id", "state"),
        Index("uq_runs_ws_idem", "workspace_id", "idempotency_key", unique=True),
        Index("ix_runs_wfv_id", "workflow_version_id"),
        Index("ix_runs_draft_id", "draft_id"),
        Index("ix_runs_approved_by", "approved_by"),
    )

    workspace_id: Mapped[UUID] = _workspace()
    workflow_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workflow_versions.id", ondelete="SET NULL")
    )
    draft_id: Mapped[UUID | None] = mapped_column(ForeignKey("drafts.id", ondelete="SET NULL"))
    state: Mapped[str] = mapped_column(String(20))
    state_since: Mapped[datetime | None]
    plan_hash: Mapped[str] = mapped_column(String(64))
    approved_by: Mapped[UUID | None] = _user_or_null()
    approved_at: Mapped[datetime | None]
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    issues: Mapped[list[Json]] = mapped_column(JsonDocument, default=list)
    finished_at: Mapped[datetime | None]


class RunNode(IdMixin, Base):
    """One node of one run. A done node keeps its outputs, so it is never executed again (P4.6)."""

    __tablename__ = "run_nodes"
    __table_args__ = (
        Index("uq_run_nodes_run_node", "run_id", "node_id", unique=True),
        Index("uq_run_nodes_idem", "idempotency_key", unique=True),
        Index("ix_run_nodes_state", "state"),
    )

    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    node_id: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(16))
    attempt: Mapped[int] = mapped_column(default=0)
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    outputs: Mapped[Json] = mapped_column(JsonDocument, default=dict)
    warnings: Mapped[list[Json]] = mapped_column(JsonDocument, default=list)
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]
    error_code: Mapped[str | None] = mapped_column(String(64))


class Artifact(IdMixin, CreatedMixin, Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        Index("ix_artifacts_run_id", "run_id"),
        Index("ix_artifacts_ws_created", "workspace_id", "created_at"),
        Index("ix_artifacts_sha256", "sha256"),
    )

    workspace_id: Mapped[UUID] = _workspace()
    run_id: Mapped[UUID | None] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    node_id: Mapped[str | None] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(32))
    format: Mapped[str] = mapped_column(String(16))
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(255))
    lineage: Mapped[Json] = mapped_column(JsonDocument)


class RunEvent(IdMixin, CreatedMixin, Base):
    __tablename__ = "run_events"
    __table_args__ = (Index("uq_run_events_run_seq", "run_id", "seq", unique=True),)

    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    seq: Mapped[int]
    type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[Json] = mapped_column(JsonDocument)


class Job(IdMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_status_run_at", "status", "run_at"),
        Index("ix_jobs_locked_until", "locked_until"),
    )

    kind: Mapped[str] = mapped_column(String(32))
    payload: Mapped[Json] = mapped_column(JsonDocument)
    run_at: Mapped[datetime]
    locked_until: Mapped[datetime | None]
    attempts: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(16))
