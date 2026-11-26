"""Alembic environment (P4.4): the app's metadata, `DATABASE_URL`, and batch mode for SQLite.

Tests pass a URL or an open connection through `config.attributes`.
"""

from alembic import context

import app.db.models  # noqa: F401  (registers every table on the metadata)
from app.config import Settings
from app.db.base import Base, UtcDateTime
from app.db.engine import make_engine, normalized_url

config = context.config


def _render_item(type_, obj, autogen_context):
    """Write `UtcDateTime` as its plain type, so migrations don't import app code."""
    if type_ == "type" and isinstance(obj, UtcDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def _configure(**kwargs) -> None:
    context.configure(
        target_metadata=Base.metadata,
        render_as_batch=True,
        render_item=_render_item,
        compare_type=True,
        **kwargs,
    )


def _url() -> str:
    return normalized_url(config.attributes.get("url") or Settings().database_url)


def run_offline() -> None:
    _configure(url=_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    connection = config.attributes.get("connection")
    if connection is None:
        with make_engine(_url()).connect() as connection:
            _run(connection)
    else:
        _run(connection)


def _run(connection) -> None:
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_offline()
else:
    run_online()
