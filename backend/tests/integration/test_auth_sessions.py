"""P5.2 sessions: refresh tokens rotate on every use, and a reused one revokes the family (T5.4)."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.auth.sessions import REFRESH_TTL, revoke, rotate, start
from app.auth.tokens import digest
from app.db import models as m
from app.db.base import Base
from app.db.engine import make_engine, make_sessions

NOW = datetime(2026, 11, 27, 12, tzinfo=UTC)


@pytest.fixture
def db(db_url):
    engine = make_engine(db_url)
    Base.metadata.create_all(engine)
    sessions = make_sessions(engine)
    with sessions.begin() as session:
        user = m.User(email="s@example.com", password_hash="x", display_name="S")
        session.add(user)
    return sessions, user.id


def test_a_session_stores_only_the_hash_of_its_refresh_token(db):
    sessions, user = db
    with sessions.begin() as session:
        row, token = start(session, user, NOW, user_agent="UA", ip_hash="h")
    assert row.refresh_hash == digest(token) != token
    assert (row.expires_at, row.user_agent) == (NOW + REFRESH_TTL, "UA")


def test_refresh_rotates_the_token(db):
    sessions, user = db
    with sessions.begin() as session:
        row, first = start(session, user, NOW)
    with sessions.begin() as session:
        rotated, second = rotate(session, first, NOW + timedelta(minutes=1))
    assert rotated.id == row.id and second != first
    with sessions.begin() as session:
        assert rotate(session, second, NOW + timedelta(minutes=2)) is not None


def test_reusing_a_rotated_token_revokes_the_whole_session(db):
    sessions, user = db
    with sessions.begin() as session:
        _, first = start(session, user, NOW)
    with sessions.begin() as session:
        _, second = rotate(session, first, NOW)
    with sessions.begin() as session:
        assert rotate(session, first, NOW) is None
    with sessions.begin() as session:
        assert rotate(session, second, NOW) is None
        assert (
            session.scalars(select(m.Session).where(m.Session.user_id == user)).one().revoked_at
            == NOW
        )


@pytest.mark.parametrize("when", ["revoked", "expired", "unknown"])
def test_a_revoked_expired_or_unknown_token_does_not_refresh(db, when):
    sessions, user = db
    with sessions.begin() as session:
        row, token = start(session, user, NOW)
    later = NOW + (REFRESH_TTL if when == "expired" else timedelta(minutes=1))
    if when == "revoked":
        with sessions.begin() as session:
            revoke(session, row.id, NOW)
    with sessions.begin() as session:
        assert rotate(session, "nope" if when == "unknown" else token, later) is None
