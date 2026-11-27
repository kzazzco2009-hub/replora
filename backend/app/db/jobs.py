"""The database job queue (T4.8; the worker that uses it is P8.2).

`claim` takes the oldest due job in one atomic `UPDATE … WHERE id = (SELECT … LIMIT 1)`. On
Postgres the inner select uses `FOR UPDATE SKIP LOCKED`, so workers take different jobs without
waiting. SQLite runs one write at a time, so the statement is serialized. A job whose lease has
expired (its worker died) can be claimed again.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Job


def enqueue(session: Session, kind: str, payload: dict[str, Any], run_at: datetime) -> Job:
    job = Job(kind=kind, payload=payload, run_at=run_at, status="queued", attempts=0)
    session.add(job)
    session.flush()
    return job


def finish(session: Session, job_id) -> None:
    """The job is done; it is never claimed again."""
    job = session.get(Job, job_id)
    job.status, job.locked_until = "done", None


def claim(sessions: sessionmaker[Session], now: datetime, lease: timedelta) -> Job | None:
    """Lease the oldest due job to this worker until `now + lease`, or None when none is due."""
    claimable = (Job.run_at <= now) & or_(
        Job.status == "queued", (Job.status == "running") & (Job.locked_until < now)
    )
    with sessions.begin() as session:
        pick = select(Job.id).where(claimable).order_by(Job.run_at, Job.id).limit(1)
        if session.get_bind().dialect.name == "postgresql":
            pick = pick.with_for_update(skip_locked=True)
        claimed = session.execute(
            update(Job)
            .where(Job.id == pick.scalar_subquery(), claimable)
            .values(status="running", locked_until=now + lease, attempts=Job.attempts + 1)
            .returning(Job.id)
        ).scalar_one_or_none()
        return None if claimed is None else session.get(Job, claimed)
