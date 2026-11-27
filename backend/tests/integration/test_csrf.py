"""P5.3 CSRF (S-25): a double-submit token on every unsafe method, plus an Origin check (T5.5)."""

import re
from http.cookies import SimpleCookie

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.base import Base
from app.db.engine import make_engine
from app.main import create_app

UNSAFE = {"post", "put", "patch", "delete"}
SALMA = {"email": "salma@example.com", "password": "a long and unusual passphrase",
         "display_name": "S", "locale": "ar"}  # fmt: skip


@pytest.fixture
def web(db_url):
    Base.metadata.create_all(make_engine(db_url))
    return TestClient(create_app(Settings(_env_file=None, database_url=db_url)))


def csrf_cookie(response):
    for header in response.headers.get_list("set-cookie"):
        cookie = SimpleCookie(header)
        if "replora_csrf" in cookie:
            return cookie["replora_csrf"]
    return None


def routes(openapi):
    for path, operations in openapi["paths"].items():
        for method in operations:
            if method in UNSAFE:
                yield method, re.sub(r"\{[^}]+\}", "01937a5e-7f00-7000-8000-000000000001", path)


def test_get_csrf_sets_a_fresh_readable_lax_cookie_on_root(web):
    first, second = web.get("/api/v1/auth/csrf"), web.get("/api/v1/auth/csrf")
    assert first.status_code == 204
    one, two = csrf_cookie(first), csrf_cookie(second)
    assert one.value != two.value and len(one.value) >= 43
    assert not one["httponly"]
    assert (one["samesite"].lower(), one["path"]) == ("lax", "/")


def test_every_unsafe_route_refuses_a_request_without_the_token(web, openapi):
    found = list(routes(openapi))
    assert len(found) > 30
    for method, path in found:
        response = web.request(method, path, json={})
        assert (response.status_code, response.json()["code"]) == (403, "CSRF_FAILED"), path


def test_a_token_that_does_not_match_the_cookie_is_refused(web):
    web.cookies.set("replora_csrf", "a" * 43)
    response = web.post("/api/v1/auth/register", json=SALMA, headers={"X-CSRF-Token": "b" * 43})
    assert (response.status_code, response.json()["code"]) == (403, "CSRF_FAILED")


def test_a_header_without_the_cookie_is_refused(web):
    response = web.post("/api/v1/auth/register", json=SALMA, headers={"X-CSRF-Token": "a" * 43})
    assert response.status_code == 403


def test_the_matching_token_passes(web):
    token = csrf_cookie(web.get("/api/v1/auth/csrf")).value
    response = web.post("/api/v1/auth/register", json=SALMA, headers={"X-CSRF-Token": token})
    assert response.status_code == 202


@pytest.mark.parametrize(("origin", "status"), [("https://evil.example", 403),
                                                ("http://localhost:3000", 202)])  # fmt: skip
def test_a_foreign_origin_is_refused_even_with_the_token(web, origin, status):
    token = csrf_cookie(web.get("/api/v1/auth/csrf")).value
    headers = {"X-CSRF-Token": token, "Origin": origin}
    assert web.post("/api/v1/auth/register", json=SALMA, headers=headers).status_code == status


def test_safe_methods_need_no_token(web):
    assert web.get("/api/v1/health").status_code == 200


def test_login_and_logout_rotate_the_token(web):
    token = csrf_cookie(web.get("/api/v1/auth/csrf")).value
    web.post("/api/v1/auth/register", json=SALMA, headers={"X-CSRF-Token": token})
    login = web.post("/api/v1/auth/login", headers={"X-CSRF-Token": token},
                        json={"email": SALMA["email"], "password": SALMA["password"]})  # fmt: skip
    rotated = csrf_cookie(login).value
    assert rotated != token
    logout = web.post("/api/v1/auth/logout", headers={"X-CSRF-Token": rotated})
    assert csrf_cookie(logout).value not in {token, rotated}
