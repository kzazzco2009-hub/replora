"""Shared fixtures: an app that never reads the developer's `.env`, its OpenAPI document, and a
database URL for the persistence tests (P4.7)."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import Settings
from app.db.engine import make_engine
from app.main import create_app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
"""Set in CI's Postgres job. Unset, every database test uses a fresh SQLite file."""


def _reset_postgres(url: str) -> None:
    engine = make_engine(url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()


@pytest.fixture
def db_url(tmp_path):
    """An empty database: a new SQLite file, or the CI Postgres with its schema reset."""
    if TEST_DATABASE_URL is None:
        yield f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
        return
    _reset_postgres(TEST_DATABASE_URL)
    yield TEST_DATABASE_URL
    _reset_postgres(TEST_DATABASE_URL)


def with_csrf(client: TestClient) -> TestClient:
    """Send the current `replora_csrf` cookie as `X-CSRF-Token`, as the browser client does."""
    client.get("/api/v1/auth/csrf")

    def copy_token(request) -> None:
        tokens = [cookie.value for cookie in client.cookies.jar if cookie.name == "replora_csrf"]
        if tokens:
            request.headers["X-CSRF-Token"] = tokens[-1]

    client.event_hooks["request"].append(copy_token)
    return client


@pytest.fixture(scope="module")
def client() -> TestClient:
    return with_csrf(TestClient(create_app(Settings(_env_file=None))))


@pytest.fixture(scope="module")
def openapi(client: TestClient) -> dict:
    return client.get("/openapi.json").json()


@pytest.fixture(scope="module")
def schemas(openapi: dict) -> dict:
    return openapi["components"]["schemas"]
