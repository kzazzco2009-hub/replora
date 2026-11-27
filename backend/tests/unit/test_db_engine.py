"""P4.1 the database engine and sessions from `DATABASE_URL`."""

from sqlalchemy import text
from sqlalchemy.pool import NullPool

from app.config import REPO_ROOT, Settings
from app.db.engine import make_engine, make_sessions, normalized_url


def test_the_default_database_is_sqlite_under_dot_data():
    url = Settings(_env_file=None).database_url
    assert url == f"sqlite:///{(REPO_ROOT / '.data' / 'replora.db').as_posix()}"


def test_sqlite_uses_wal_and_enforces_foreign_keys(tmp_path):
    engine = make_engine(f"sqlite:///{(tmp_path / 'x.db').as_posix()}")
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_postgres_uses_psycopg_3_and_no_pool_for_serverless():
    engine = make_engine("postgresql://u:p@db.example:5432/replora")
    assert (engine.dialect.name, engine.dialect.driver) == ("postgresql", "psycopg")
    assert isinstance(engine.pool, NullPool)


def test_a_plain_postgres_url_gets_the_psycopg_driver():
    assert normalized_url("postgres://u@h/db") == "postgresql+psycopg://u@h/db"
    assert normalized_url("postgresql://u@h/db") == "postgresql+psycopg://u@h/db"
    assert normalized_url("postgresql+psycopg://u@h/db") == "postgresql+psycopg://u@h/db"
    assert normalized_url("sqlite:///x.db") == "sqlite:///x.db"


def test_sessions_keep_loaded_values_after_commit(tmp_path):
    sessions = make_sessions(make_engine(f"sqlite:///{(tmp_path / 'x.db').as_posix()}"))
    with sessions() as session:
        assert session.execute(text("SELECT 1")).scalar() == 1
    assert sessions.kw["expire_on_commit"] is False
