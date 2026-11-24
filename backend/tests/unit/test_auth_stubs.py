"""P0.5: the §2 auth contract is served as 501 stubs and documented in OpenAPI."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

SESSION_ID = "01937a5e-7f00-7000-8000-000000000001"
PASSWORD = "correct horse battery staple"

# (method, path, success status, sample valid body) — docs/api_contract.md §2.
AUTH_ENDPOINTS = [
    ("get", "/api/v1/auth/csrf", 204, None),
    (
        "post",
        "/api/v1/auth/register",
        201,
        {"email": "a@example.com", "password": PASSWORD, "display_name": "A", "locale": "ar"},
    ),
    ("post", "/api/v1/auth/login", 200, {"email": "a@example.com", "password": PASSWORD}),
    ("post", "/api/v1/auth/logout", 204, None),
    ("post", "/api/v1/auth/refresh", 204, None),
    ("get", "/api/v1/auth/me", 200, None),
    ("patch", "/api/v1/auth/me", 200, {"timezone": "Africa/Cairo"}),
    ("delete", "/api/v1/auth/me", 202, {"password": PASSWORD}),
    ("post", "/api/v1/auth/verify-email", 204, {"token": "t"}),
    ("post", "/api/v1/auth/password/forgot", 202, {"email": "a@example.com"}),
    ("post", "/api/v1/auth/password/reset", 204, {"token": "t", "password": PASSWORD}),
    ("post", "/api/v1/auth/mfa/enroll", 200, None),
    ("post", "/api/v1/auth/mfa/enroll/confirm", 204, {"code": "123456"}),
    ("post", "/api/v1/auth/mfa/challenge", 200, {"code": "123456"}),
    ("delete", "/api/v1/auth/mfa", 204, {"password": PASSWORD, "code": "123456"}),
    ("post", "/api/v1/auth/me/export", 202, None),
    ("get", f"/api/v1/auth/me/export/{SESSION_ID}", 200, None),
    ("get", "/api/v1/auth/sessions", 200, None),
    ("delete", f"/api/v1/auth/sessions/{SESSION_ID}", 204, None),
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app(Settings(_env_file=None)))


@pytest.fixture(scope="module")
def openapi(client: TestClient) -> dict:
    return client.get("/openapi.json").json()


def openapi_path(path: str) -> str:
    """Turn a concrete test path back into its OpenAPI template."""
    return path.replace(SESSION_ID, "{export_id}" if "/export/" in path else "{session_id}")


@pytest.mark.parametrize(("method", "path", "status", "body"), AUTH_ENDPOINTS)
def test_auth_endpoint_is_documented_with_its_success_status(openapi, method, path, status, body):
    operation = openapi["paths"][openapi_path(path)][method]

    assert str(status) in operation["responses"]


@pytest.mark.parametrize(("method", "path", "status", "body"), AUTH_ENDPOINTS)
def test_auth_stub_answers_501_problem_json(client, method, path, status, body):
    response = client.request(method, path, json=body)

    assert response.status_code == 501
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Not implemented",
        "status": 501,
        "code": "NOT_IMPLEMENTED",
    }


def test_all_contract_auth_paths_and_nothing_else(openapi):
    documented = {
        (method, path)
        for path, operations in openapi["paths"].items()
        if path.startswith("/api/v1/auth/")
        for method in operations
    }

    assert documented == {(m, openapi_path(p)) for m, p, _, _ in AUTH_ENDPOINTS}


def test_user_schema_matches_contract(openapi):
    user = openapi["components"]["schemas"]["User"]

    assert set(user["properties"]) == {
        "id", "email", "display_name", "locale", "theme", "timezone",
        "mfa_enabled", "email_verified", "created_at",
    }  # fmt: skip
    assert user["properties"]["locale"]["enum"] == ["ar", "en"]
    assert user["properties"]["theme"]["enum"] == ["light", "dark", "system"]


def test_login_documents_user_or_mfa_challenge(openapi):
    login = openapi["paths"]["/api/v1/auth/login"]["post"]
    schema = login["responses"]["200"]["content"]["application/json"]["schema"]

    assert {option["$ref"].rsplit("/", 1)[1] for option in schema["anyOf"]} == {
        "User",
        "MfaRequired",
    }


def test_errors_are_documented_as_problem_json(openapi):
    responses = openapi["paths"]["/api/v1/auth/login"]["post"]["responses"]

    for status in ("4XX", "501"):
        assert set(responses[status]["content"]) == {"application/problem+json"}


def test_register_rejects_a_password_shorter_than_12(client):
    body = {"email": "a@example.com", "password": "short", "display_name": "A", "locale": "en"}

    assert client.post("/api/v1/auth/register", json=body).status_code == 422


def test_request_bodies_reject_unknown_fields(client):
    body = {"email": "a@example.com", "password": PASSWORD, "remember_me": True}

    assert client.post("/api/v1/auth/login", json=body).status_code == 422
