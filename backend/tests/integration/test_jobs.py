"""T4.8: two workers never claim the same job (Postgres SKIP LOCKED; SQLite serialized)."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest

from app.db.base import Base
from app.db.engine import make_engine, make_sessions
from app.db.jobs import claim, enqueue

NOW = datetime(2026, 11, 27, 12, tzinfo=UTC)
LEASE = timedelta(minutes=5)


@pytest.fixture
def sessions(tmp_path):
    engine = make_engine(f"sqlite:///{(tmp_path / 'j.db').as_posix()}")
    Base.metadata.create_all(engine)
    return make_sessions(engine)


def add(sessions, count, at=NOW):
    with sessions.begin() as session:
        return [enqueue(session, "node", {"n": k}, at).id for k in range(count)]


def test_the_oldest_due_job_is_claimed_and_leased(sessions):
    first, second = add(sessions, 1, NOW - timedelta(minutes=2)) + add(sessions, 1, NOW)
    job = claim(sessions, NOW, LEASE)
    assert (job.id, job.status, job.attempts, job.locked_until) == (
        first,
        "running",
        1,
        NOW + LEASE,
    )
    assert claim(sessions, NOW, LEASE).id == second
    assert claim(sessions, NOW, LEASE) is None


def test_a_job_due_later_is_not_claimed(sessions):
    add(sessions, 1, NOW + timedelta(seconds=1))
    assert claim(sessions, NOW, LEASE) is None


def test_a_job_whose_lease_expired_is_claimed_again(sessions):
    (job_id,) = add(sessions, 1)
    claim(sessions, NOW, LEASE)
    assert claim(sessions, NOW + LEASE, LEASE) is None
    again = claim(sessions, NOW + LEASE + timedelta(seconds=1), LEASE)
    assert (again.id, again.attempts) == (job_id, 2)


def test_two_workers_never_claim_the_same_job(sessions):
    ids = set(add(sessions, 40))

    def worker() -> list:
        claimed = []
        while (job := claim(sessions, NOW, LEASE)) is not None:
            claimed.append(job.id)
        return claimed

    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = pool.submit(worker), pool.submit(worker)
        first, second = a.result(), b.result()
    assert len(first) + len(second) == len(ids)
    assert set(first) | set(second) == ids
    assert set(first).isdisjoint(second)
