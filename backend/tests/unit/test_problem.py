"""Every error answers problem+json: routing errors, HTTPException and unhandled exceptions."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.problem import validation_code
from app.config import Settings
from app.main import create_app


def _boom() -> None:
    raise RuntimeError("secret internal state")


def _teapot() -> None:
    raise HTTPException(418, detail="internal detail", headers={"X-Extra": "1"})


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app(Settings(_env_file=None))
    app.add_api_route("/test/boom", _boom, tags=["test"])
    app.add_api_route("/test/teapot", _teapot, tags=["test"])
    return TestClient(app, raise_server_exceptions=False)


def assert_problem(response, status: int, code: str) -> dict:
    assert response.status_code == status
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["status"] == status
    assert body["code"] == code
    assert body["type"] == "about:blank"
    return body


def test_unknown_path_is_404_problem_json(client):
    body = assert_problem(client.get("/api/v1/nope"), 404, "NOT_FOUND")

    assert body["title"] == "Not Found"


def test_wrong_method_is_405_problem_json_and_keeps_allow(client):
    response = client.put("/api/v1/health")

    assert_problem(response, 405, "METHOD_NOT_ALLOWED")
    assert response.headers["allow"] == "GET"


def test_http_exception_keeps_headers_and_hides_detail(client):
    response = client.get("/test/teapot")

    assert_problem(response, 418, "IM_A_TEAPOT")
    assert response.headers["x-extra"] == "1"
    assert "internal detail" not in response.text


def test_unhandled_exception_is_500_problem_json_without_internals(client):
    response = client.get("/test/boom")

    body = assert_problem(response, 500, "INTERNAL_ERROR")
    assert body["title"] == "Internal Server Error"
    assert "secret" not in response.text


def test_unknown_validation_type_falls_back_to_invalid():
    assert validation_code("some_future_pydantic_type") == "INVALID"
