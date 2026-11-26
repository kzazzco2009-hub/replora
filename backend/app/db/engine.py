"""The engine and sessions from `DATABASE_URL` (P4.1).

SQLite (local) runs in WAL mode with foreign keys enforced on every connection. Postgres uses
psycopg 3 and `NullPool`: on serverless each invocation is short, and the Supabase pooler does the
pooling, so connections are not kept between requests.
"""

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

POSTGRES_PREFIXES = ("postgres://", "postgresql://")


def normalized_url(url: str) -> str:
    """Give a plain Postgres URL (as Supabase shows it) the psycopg 3 driver."""
    for prefix in POSTGRES_PREFIXES:
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    return url


def make_engine(url: str) -> Engine:
    url = normalized_url(url)
    if not url.startswith("sqlite"):
        return create_engine(url, poolclass=NullPool)
    engine = create_engine(url)
    event.listen(engine, "connect", _sqlite_pragmas)
    return engine


def _sqlite_pragmas(connection, _record) -> None:
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def make_sessions(engine: Engine) -> sessionmaker[Session]:
    """Sessions that keep loaded values after commit, so results can be returned as they are."""
    return sessionmaker(engine, expire_on_commit=False)
