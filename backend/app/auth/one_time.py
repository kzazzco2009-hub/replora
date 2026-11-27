"""One-time tokens for email verification and password reset (P5.4, S-27).

A token is 256 random bits sent by email. The database keeps only its SHA-256, the kind, a
30-minute expiry, and when it was used. It works once, for its own kind only.
"""

from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.tokens import digest, new_secret
from app.db import models as m

TOKEN_TTL = timedelta(minutes=30)
TokenKind = Literal["verify", "reset"]


def issue(session: Session, user: m.User, kind: TokenKind, now: datetime) -> str:
    token = new_secret()
    session.add(m.AuthToken(user_id=user.id, kind=kind, token_hash=digest(token),
                            expires_at=now + TOKEN_TTL))  # fmt: skip
    return token


def redeem(session: Session, kind: TokenKind, token: str, now: datetime) -> m.User | None:
    """The token's user, marking it used; None if unknown, of another kind, used or expired."""
    row = session.scalars(
        select(m.AuthToken).where(m.AuthToken.token_hash == digest(token), m.AuthToken.kind == kind)
    ).one_or_none()
    if row is None or row.used_at is not None or row.expires_at <= now:
        return None
    row.used_at = now
    user = session.get(m.User, row.user_id)
    return None if user is None or user.deleted_at is not None else user


def revoke_all_sessions(session: Session, user: m.User, now: datetime) -> None:
    """S-27: a new password ends every session."""
    session.execute(
        update(m.Session)
        .where(m.Session.user_id == user.id, m.Session.revoked_at.is_(None))
        .values(revoked_at=now)
    )
