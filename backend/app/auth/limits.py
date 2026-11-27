"""Database rate limits (P5.7, S-26): fixed windows counted in `rate_limits`.

Login failures: 5 per 15 minutes, per account and per IP. Register and forgot-password: 3 per hour
per IP. Over the limit is 429 `RATE_LIMITED` with `Retry-After`, until the window ends. IPs are
stored only as an HMAC, never raw.
"""

import hashlib
import hmac
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.api.problem import ProblemError
from app.db import models as m


@dataclass(frozen=True)
class Rule:
    name: str
    limit: int
    window: timedelta


LOGIN = Rule("login", 5, timedelta(minutes=15))
REGISTER = Rule("register", 3, timedelta(hours=1))
FORGOT = Rule("forgot", 3, timedelta(hours=1))


def ip_hash(ip: str, key: str) -> str:
    return hmac.new(key.encode(), ip.encode(), hashlib.sha256).hexdigest()


def _start(rule: Rule, now: datetime) -> datetime:
    seconds = int(rule.window.total_seconds())
    return datetime.fromtimestamp(int(now.timestamp()) // seconds * seconds, UTC)


def _key(rule: Rule, subject: str) -> str:
    return f"{rule.name}:{subject}"


def used(session: Session, rule: Rule, subject: str, now: datetime) -> int:
    row = session.get(m.RateLimit, (_key(rule, subject), _start(rule, now)))
    return 0 if row is None else row.count


def hit(session: Session, rule: Rule, subject: str, now: datetime) -> None:
    """Count one more, atomically (an upsert), so concurrent hits are never lost."""
    insert = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    statement = insert(m.RateLimit).values(key=_key(rule, subject), window_start=_start(rule, now),
                                           count=1)  # fmt: skip
    session.execute(statement.on_conflict_do_update(
        index_elements=["key", "window_start"], set_={"count": m.RateLimit.count + 1}
    ))  # fmt: skip


def over(session: Session, rule: Rule, subjects: list[str], now: datetime) -> ProblemError | None:
    """The 429 to answer when any subject has used up its window, else None."""
    if all(used(session, rule, subject, now) < rule.limit for subject in subjects):
        return None
    wait = _start(rule, now) + rule.window - now
    headers = {"Retry-After": str(max(1, math.ceil(wait.total_seconds())))}
    return ProblemError(429, "RATE_LIMITED", "Too many requests", headers)
