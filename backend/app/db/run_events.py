"""Run events (§7 polling): one row per change, numbered 1, 2, … within the run."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models as m


def emit(session: Session, run_id: UUID, kind: str, at: datetime, node_id: str | None = None,
         **payload: Any) -> None:  # fmt: skip
    """Append an event. The caller holds the run (it was read in this transaction)."""
    last = session.scalar(select(func.max(m.RunEvent.seq)).where(m.RunEvent.run_id == run_id))
    session.add(m.RunEvent(run_id=run_id, seq=(last or 0) + 1, type=kind, node_id=node_id,
                           payload=payload, created_at=at))  # fmt: skip
