"""P0.5: the §2 auth contract is served as 501 stubs and documented in OpenAPI."""

import re

import pytest

SESSION_ID = "01937a5e-7f00-7000-8000-000000000001"
PASSWORD = "correct horse battery staple"

# (method, path, success status, sample valid body) — docs/api_contract.md §2.
AUTH_ENDPOINTS = [
    ("get", "/api/v1/auth/csrf", 204, None),
    (
        "post",
        "/api/v1/auth/register",
        202,
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


def openapi_path(path: str) -> str:
    """Turn a concrete test path back into its OpenAPI template."""
    return path.replace(SESSION_ID, "{export_id}" if "/export/" in path else "{session_id}")


@pytest.mark.parametrize(("method", "path", "status", "body"), AUTH_ENDPOINTS)
def test_auth_endpoint_is_documented_with_its_success_status(openapi, method, path, status, body):
    operation = openapi["paths"][openapi_path(path)][method]

    assert str(status) in operation["responses"]


IMPLEMENTED = {"/api/v1/auth/csrf", "/api/v1/auth/register", "/api/v1/auth/login",
               "/api/v1/auth/logout", "/api/v1/auth/refresh",
               ("get", "/api/v1/auth/me")}  # fmt: skip
"""Phase 5 endpoints that are real now; the rest still answer 501."""
STUBS = [e for e in AUTH_ENDPOINTS
         if e[1] not in IMPLEMENTED and (e[0], e[1]) not in IMPLEMENTED]  # fmt: skip


@pytest.mark.parametrize(("method", "path", "status", "body"), STUBS)
def test_auth_stub_answers_501_problem_json(client, method, path, status, body):
    response = client.request(method, path, json=body)

    assert response.status_code == 501
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Not implemented",
        "status": 501,
        "code": "NOT_IMPLEMENTED",
        "correlation_id": response.headers["x-request-id"],
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


ERROR_STATUSES = ("401", "403", "409", "422", "429", "501")
PROBLEM_REF = {"$ref": "#/components/schemas/ProblemDetails"}


@pytest.mark.parametrize(("method", "path", "status", "body"), AUTH_ENDPOINTS)
def test_errors_are_documented_as_problem_details(openapi, method, path, status, body):
    responses = openapi["paths"][openapi_path(path)][method]["responses"]

    for error in ERROR_STATUSES:
        assert responses[error]["content"] == {"application/problem+json": {"schema": PROBLEM_REF}}


def test_problem_details_schema_carries_code_and_correlation_id(openapi):
    properties = openapi["components"]["schemas"]["ProblemDetails"]["properties"]

    assert {"type", "title", "status", "code", "correlation_id", "errors"} <= set(properties)


def test_fastapi_default_validation_schema_is_not_exposed(openapi):
    assert "HTTPValidationError" not in openapi["components"]["schemas"]


def test_validation_error_is_problem_json_with_field_paths(client):
    response = client.post("/api/v1/auth/login", json={"email": "not-an-email"})

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["code"] == "VALIDATION_FAILED"
    assert {error["path"] for error in body["errors"]} == {"body.email", "body.password"}


def test_validation_error_never_echoes_the_input(client):
    secret = "tiny-secret"  # 11 characters: below the 12-character minimum
    body = {"email": "a@example.com", "password": secret, "display_name": "A", "locale": "en"}

    response = client.post("/api/v1/auth/register", json=body)

    assert response.status_code == 422
    assert secret not in response.text


def test_operation_ids_are_short_stable_and_unique(openapi):
    ids = [op["operationId"] for ops in openapi["paths"].values() for op in ops.values()]

    assert len(ids) == len(set(ids))
    assert openapi["paths"]["/api/v1/auth/login"]["post"]["operationId"] == "auth_login"
    assert openapi["paths"]["/api/v1/health"]["get"]["operationId"] == "health_get"
    assert all(re.fullmatch(r"[a-z]+_[a-z_]+", operation_id) for operation_id in ids)


def test_register_rejects_a_password_shorter_than_12(client):
    body = {"email": "a@example.com", "password": "short", "display_name": "A", "locale": "en"}

    assert client.post("/api/v1/auth/register", json=body).status_code == 422


def test_request_bodies_reject_unknown_fields(client):
    body = {"email": "a@example.com", "password": PASSWORD, "remember_me": True}

    assert client.post("/api/v1/auth/login", json=body).status_code == 422


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/auth/me/export/{export_id}"),
        ("delete", "/api/v1/auth/sessions/{session_id}"),
    ],
)
def test_lookup_by_id_documents_404_as_problem_details(openapi, method, path):
    responses = openapi["paths"][path][method]["responses"]

    assert responses["404"]["content"] == {"application/problem+json": {"schema": PROBLEM_REF}}


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("delete", "/api/v1/auth/me", {"password": "p" * 257}),
        ("delete", "/api/v1/auth/mfa", {"password": "p" * 257, "code": "123456"}),
        ("post", "/api/v1/auth/login", {"email": "a@example.com", "password": "p" * 257}),
    ],
)
def test_password_fields_reject_more_than_256_characters(client, method, path, body):
    response = client.request(method, path, json=body)

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "body.password", "code": "STRING_TOO_LONG", "params": {"max_length": 256}}
    ]


# One request per validation code our models can produce today. The codes are an explicit
# list (problem.VALIDATION_CODES), so a Pydantic upgrade that renames a type fails here.
VALIDATION_CASES = [
    ("post", "/api/v1/auth/login", {"json": {"password": PASSWORD}}, "body.email", "MISSING"),
    ("post", "/api/v1/auth/login", {}, "body", "MISSING"),
    (
        "post",
        "/api/v1/auth/login",
        {"json": {"email": "a@example.com", "password": PASSWORD, "x": 1}},
        "body.x",
        "EXTRA_FORBIDDEN",
    ),
    (
        "post",
        "/api/v1/auth/password/forgot",
        {"json": {"email": "x"}},
        "body.email",
        "INVALID_EMAIL",
    ),
    ("post", "/api/v1/auth/password/forgot", {"json": {"email": 5}}, "body.email", "INVALID_EMAIL"),
    ("post", "/api/v1/auth/verify-email", {"json": {"token": 5}}, "body.token", "STRING_TYPE"),
    (
        "post",
        "/api/v1/auth/mfa/challenge",
        {"json": {}},
        "body",
        "MFA_CODE_OR_RECOVERY_REQUIRED",
    ),
    ("post", "/api/v1/auth/password/forgot", {"json": [1]}, "body", "MODEL_ATTRIBUTES_TYPE"),
    (
        "post",
        "/api/v1/auth/password/forgot",
        {"content": b"{bad", "headers": {"content-type": "application/json"}},
        "body.1",
        "JSON_INVALID",
    ),
    ("delete", "/api/v1/auth/me", {"json": {"password": ""}}, "body.password", "STRING_TOO_SHORT"),
    (
        "delete",
        "/api/v1/auth/me",
        {"json": {"password": "p" * 257}},
        "body.password",
        "STRING_TOO_LONG",
    ),
    (
        "post",
        "/api/v1/auth/mfa/enroll/confirm",
        {"json": {"code": "12"}},
        "body.code",
        "STRING_PATTERN_MISMATCH",
    ),
    ("patch", "/api/v1/auth/me", {"json": {"locale": "fr"}}, "body.locale", "LITERAL_ERROR"),
    ("get", "/api/v1/auth/me/export/x", {}, "path.export_id", "UUID_PARSING"),
]


@pytest.mark.parametrize(("method", "path", "request_args", "field", "code"), VALIDATION_CASES)
def test_validation_codes_are_explicit_and_stable(client, method, path, request_args, field, code):
    response = client.request(method, path, **request_args)

    assert response.status_code == 422
    assert (field, code) in {(e["path"], e["code"]) for e in response.json()["errors"]}


@pytest.mark.parametrize(
    "body", [{}, {"code": "123456", "recovery_code": "abcd-efgh"}], ids=["neither", "both"]
)
def test_mfa_challenge_needs_exactly_one_of_code_or_recovery_code(client, body):
    response = client.post("/api/v1/auth/mfa/challenge", json=body)

    assert response.status_code == 422
    assert response.json()["errors"] == [
        {"path": "body", "code": "MFA_CODE_OR_RECOVERY_REQUIRED", "params": {}}
    ]


@pytest.mark.parametrize(
    ("body", "field"),
    [({"code": "12"}, "body.code"), ({"recovery_code": ""}, "body.recovery_code")],
)
def test_mfa_challenge_field_errors_use_form_field_paths(client, body, field):
    response = client.post("/api/v1/auth/mfa/challenge", json=body)

    assert [error["path"] for error in response.json()["errors"]] == [field]


def test_mfa_challenge_accepts_a_recovery_code(client):
    response = client.post("/api/v1/auth/mfa/challenge", json={"recovery_code": "abcd-efgh"})

    assert response.status_code == 501


def test_email_keeps_its_openapi_format(openapi):
    email = openapi["components"]["schemas"]["EmailRequest"]["properties"]["email"]

    assert email["format"] == "email"


def test_register_answers_like_forgot_password_so_it_never_reveals_an_account(openapi):
    paths = openapi["paths"]
    register = paths["/api/v1/auth/register"]["post"]["responses"]
    forgot = paths["/api/v1/auth/password/forgot"]["post"]["responses"]

    assert "201" not in register
    assert register["202"] == forgot["202"]
    assert register["202"]["content"]["application/json"]["schema"] == {}


# Endpoints that check a secret answer 400 when it is wrong; 401 only means "no session".
SECRET_CHECKS = [
    ("post", "/api/v1/auth/verify-email"),
    ("post", "/api/v1/auth/password/reset"),
    ("post", "/api/v1/auth/mfa/enroll/confirm"),
    ("post", "/api/v1/auth/mfa/challenge"),
    ("delete", "/api/v1/auth/mfa"),
    ("delete", "/api/v1/auth/me"),
]


@pytest.mark.parametrize(("method", "path"), SECRET_CHECKS)
def test_a_wrong_secret_is_documented_as_400(openapi, method, path):
    response = openapi["paths"][path][method]["responses"]["400"]

    assert "ProblemDetails" in response["content"]["application/problem+json"]["schema"]["$ref"]
