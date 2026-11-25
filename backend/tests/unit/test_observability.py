"""T0.7 (S‑87): every response has an `X-Request-ID`, logs are JSON with the same ID, and no PII."""

import io
import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.observability import JsonFormatter

PASSWORD = "correct horse battery staple"
EMAIL = "someone@example.com"


def _boom() -> None:
    raise RuntimeError("secret internal state")


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app(Settings(_env_file=None))
    app.add_api_route("/test/boom", _boom, tags=["test"])
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def log_lines():
    """Collect what the app logs, formatted exactly as in production."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    yield lambda: [json.loads(line) for line in stream.getvalue().splitlines()]
    root.removeHandler(handler)


REQUESTS = [
    ("get", "/api/v1/health", 200),
    ("get", "/api/v1/nope", 404),
    ("post", "/api/v1/auth/login", 422),
    ("get", "/api/v1/auth/me", 501),
    ("get", "/test/boom", 500),
]


@pytest.mark.parametrize(("method", "path", "status"), REQUESTS)
def test_every_response_has_a_request_id(client, method, path, status):
    response = client.request(method, path)

    assert response.status_code == status
    assert len(response.headers["x-request-id"]) == 36  # a UUID


@pytest.mark.parametrize(("method", "path", "status"), REQUESTS[1:])
def test_problem_json_carries_the_same_id_as_correlation_id(client, method, path, status):
    response = client.request(method, path)

    assert response.json()["correlation_id"] == response.headers["x-request-id"]


def test_each_request_gets_a_new_id(client):
    first = client.get("/api/v1/health").headers["x-request-id"]

    assert client.get("/api/v1/health").headers["x-request-id"] != first


def test_a_well_formed_incoming_id_is_kept(client):
    response = client.get("/api/v1/health", headers={"X-Request-ID": "edge-01J9.abc_1"})

    assert response.headers["x-request-id"] == "edge-01J9.abc_1"


@pytest.mark.parametrize("bad", ["x" * 65, "has space", "line\nbreak", ""])
def test_a_malformed_incoming_id_is_replaced(client, bad):
    response = client.get("/api/v1/health", headers={"X-Request-ID": bad})

    assert response.headers["x-request-id"] != bad
    assert len(response.headers["x-request-id"]) == 36


def test_the_access_log_is_json_with_the_request_id(client, log_lines):
    response = client.get("/api/v1/health?cursor=opaque")

    access = [line for line in log_lines() if line["message"] == "request"]
    assert access == [
        {
            "level": "INFO",
            "logger": "app.access",
            "message": "request",
            "request_id": response.headers["x-request-id"],
            "method": "GET",
            "path": "/api/v1/health",
            "status": 200,
            "duration_ms": access[0]["duration_ms"],
            "time": access[0]["time"],
        }
    ]


def test_a_login_request_logs_no_password_and_no_email(client, log_lines):
    client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})

    logged = "\n".join(json.dumps(line) for line in log_lines())
    assert '"path": "/api/v1/auth/login"' in logged
    assert PASSWORD not in logged
    assert EMAIL not in logged


def test_an_unhandled_error_is_logged_with_its_id_but_not_sent(client, log_lines):
    response = client.get("/test/boom")

    errors = [line for line in log_lines() if line["level"] == "ERROR"]
    assert "secret internal state" not in response.text
    assert any("secret internal state" in line.get("exception", "") for line in errors)
    assert all(line["request_id"] == response.headers["x-request-id"] for line in errors)


def test_the_formatter_scrubs_sensitive_fields_and_emails():
    record = logging.LogRecord("app", logging.INFO, __file__, 1, f"invite for {EMAIL}", None, None)
    record.password = PASSWORD
    record.headers = {"cookie": "replora_access=abc", "accept": "*/*"}

    line = json.loads(JsonFormatter().format(record))

    assert line["message"] == "invite for [email]"
    assert line["password"] == "[redacted]"
    assert line["headers"] == {"cookie": "[redacted]", "accept": "*/*"}
