"""P4.4 Alembic: upgrade, downgrade, upgrade again (T4.1), and no drift from the models (T4.2)."""

from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.engine import make_engine

BACKEND = Path(__file__).resolve().parents[2]


@pytest.fixture
def url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'm.db').as_posix()}"


def alembic(url: str) -> Config:
    config = Config(BACKEND / "alembic.ini")
    config.attributes["url"] = url
    return config


def tables(url: str) -> set[str]:
    return set(inspect(make_engine(url)).get_table_names()) - {"alembic_version"}


def test_upgrade_downgrade_and_upgrade_again(url):
    command.upgrade(alembic(url), "head")
    assert tables(url) == set(Base.metadata.tables)
    command.downgrade(alembic(url), "base")
    assert tables(url) == set()
    command.upgrade(alembic(url), "head")
    assert tables(url) == set(Base.metadata.tables)


@pytest.mark.filterwarnings("ignore:autogenerate skipping metadata-specified expression")
@pytest.mark.filterwarnings("ignore:Skipped unsupported reflection of expression-based index")
def test_the_migrations_match_the_models(url):
    command.upgrade(alembic(url), "head")
    with make_engine(url).connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_the_migrated_schema_keeps_emails_unique_ignoring_case(url):
    command.upgrade(alembic(url), "head")
    insert = text("INSERT INTO users (id, email, password_hash, locale, theme, timezone, "
                  "created_at) VALUES (:id, :email, 'x', 'ar', 'system', 'UTC', "
                  "'2026-11-26 12:00:00+00:00')")  # fmt: skip
    with make_engine(url).begin() as connection:
        connection.execute(insert, {"id": "0" * 32, "email": "Salma@Example.com"})
    with pytest.raises(IntegrityError), make_engine(url).begin() as connection:
        connection.execute(insert, {"id": "1" * 32, "email": "salma@example.COM"})
