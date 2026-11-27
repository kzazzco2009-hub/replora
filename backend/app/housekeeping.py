"""Scheduled jobs (P8.2): what must happen even when nobody opens the run, file or account.

- approval expiry: a run left in `AWAITING_APPROVAL` past `APPROVAL_TTL_HOURS` becomes
  `EXPIRED`, with its `state_changed` event (the API also expires it lazily on approve);
- file retention (P6.6) and account purge after the grace period (P5.10, S-29).

The worker runs them every `EVERY`; on Vercel a cron calls the same function (P8.8).
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.auth.privacy import purge_deleted
from app.config import Settings
from app.core.engine.run import expire_if_stale
from app.core.run_state import RunState
from app.db import models as m
from app.db.engine_state import apply, load_run
from app.db.run_events import emit
from app.files.service import purge_expired

EVERY = timedelta(minutes=1)


def expire_stale_runs(session: Session, now: datetime, ttl: timedelta) -> int:
    """Expire every run, in any workspace, that has awaited approval for longer than `ttl`."""
    stale = (m.Run.state == RunState.AWAITING_APPROVAL) & (m.Run.state_since < now - ttl)
    rows = session.scalars(select(m.Run).where(stale)).all()
    for row in rows:
        apply(row, expire_if_stale(load_run(session, row.workspace_id, row.id), now, ttl))
        emit(session, row.id, "state_changed", now, state=row.state)
    return len(rows)


def housekeep(sessions: sessionmaker[Session], storage, settings: Settings,
              now: datetime) -> dict[str, int]:  # fmt: skip
    """Run every scheduled job once, each in its own transaction. The counts, for the log."""
    with sessions.begin() as session:
        expired = expire_stale_runs(session, now, settings.approval_ttl)
    with sessions.begin() as session:
        files = purge_expired(session, storage, now)
    with sessions.begin() as session:
        users = purge_deleted(session, storage, now, settings.deletion_grace)
    return {"expired_runs": expired, "purged_files": files, "purged_users": users}
