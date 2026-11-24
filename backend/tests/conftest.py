"""Shared fixtures: an app that never reads the developer's `.env`, and its OpenAPI document."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app(Settings(_env_file=None)))


@pytest.fixture(scope="module")
def openapi(client: TestClient) -> dict:
    return client.get("/openapi.json").json()


@pytest.fixture(scope="module")
def schemas(openapi: dict) -> dict:
    return openapi["components"]["schemas"]
