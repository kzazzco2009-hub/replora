"""T0.1: `GET /api/v1/health` reports liveness and the backend version."""

from importlib.metadata import version

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_returns_ok_and_package_version():
    client = TestClient(create_app(Settings(_env_file=None)))

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": version("replora-backend")}
