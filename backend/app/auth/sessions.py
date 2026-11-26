"""Login sessions (P5.2, S-24): rotating refresh tokens with reuse detection.

A session keeps the hash of its current refresh token. Each refresh moves that hash to
`used_refresh_tokens` and issues a new token. If a used token comes back, someone has a copy, so
the whole session is revoked and both holders must sign in again (T5.4).
"""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.tokens import digest, new_secret
from app.db import models as m

REFRESH_TTL = timedelta(days=30)


def start(
    session: Session,
    user_id: UUID,
    now: datetime,
    user_agent: str | None = None,
    ip_hash: str | None = None,
) -> tuple[m.Session, str]:
    """A new session and its refresh token. Only the token's hash is stored."""
    token = new_secret()
    row = m.Session(user_id=user_id, refresh_hash=digest(token), expires_at=now + REFRESH_TTL,
                    user_agent=user_agent, ip_hash=ip_hash)  # fmt: skip
    session.add(row)
    session.flush()
    return row, token


def rotate(session: Session, token: str, now: datetime) -> tuple[m.Session, str] | None:
    """The session and a new refresh token, or None (and a revoked session on reuse)."""
    hashed = digest(token)
    row = session.scalars(select(m.Session).where(m.Session.refresh_hash == hashed)).one_or_none()
    if row is None:
        used = session.scalars(
            select(m.UsedRefreshToken).where(m.UsedRefreshToken.token_hash == hashed)
        ).one_or_none()
        if used is not None:
            revoke(session, used.session_id, now)
        return None
    if row.revoked_at is not None or row.expires_at <= now:
        return None
    session.add(m.UsedRefreshToken(session_id=row.id, token_hash=hashed, used_at=now))
    fresh = new_secret()
    row.refresh_hash = digest(fresh)
    return row, fresh


def revoke(session: Session, session_id: UUID, now: datetime) -> None:
    row = session.get(m.Session, session_id)
    if row is not None and row.revoked_at is None:
        row.revoked_at = now
