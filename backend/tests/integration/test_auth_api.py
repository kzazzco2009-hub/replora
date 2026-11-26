"""P5.2 the session endpoints: register, login, me, refresh, logout (T5.3), cookies (T5.6)."""

from http.cookies import SimpleCookie

import pytest
from conftest import with_csrf
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.base import Base
from app.db.engine import make_engine
from app.main import create_app

PASSWORD = "a long and unusual passphrase"
SALMA = {"email": "Salma@Example.com", "password": PASSWORD, "display_name": "سلمى",
         "locale": "ar"}  # fmt: skip


def app_client(db_url: str, **settings) -> TestClient:
    Base.metadata.create_all(make_engine(db_url))
    app = create_app(Settings(_env_file=None, database_url=db_url, **settings))
    # Secure cookies only come back over https, as in production.
    https = settings.get("app_env") == "production"
    return with_csrf(
        TestClient(app, base_url="https://testserver" if https else "http://testserver")
    )


@pytest.fixture
def client(db_url):
    return app_client(db_url)


def login(client, email="salma@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def set_cookies(response) -> dict[str, SimpleCookie]:
    found = {}
    for header in response.headers.get_list("set-cookie"):
        cookie = SimpleCookie(header)
        found.update({name: cookie for name in cookie})
    return found


def test_register_then_login_gives_the_user_and_session_cookies(client):
    assert client.post("/api/v1/auth/register", json=SALMA).status_code == 202
    response = login(client)
    assert response.status_code == 200
    user = response.json()
    assert (user["email"], user["display_name"], user["locale"]) == (
        "salma@example.com", "سلمى", "ar")  # fmt: skip
    assert (user["email_verified"], user["mfa_enabled"]) == (False, False)
    assert {"replora_access", "replora_refresh"} <= set(set_cookies(response))


def test_me_shows_the_personal_workspace_where_the_user_is_owner(client):
    client.post("/api/v1/auth/register", json=SALMA)
    login(client)
    me = client.get("/api/v1/auth/me").json()
    assert [(w["name"], w["role"]) for w in me["memberships"]] == [("سلمى", "owner")]


def test_register_answers_202_for_an_existing_email_and_keeps_the_first_account(client):
    client.post("/api/v1/auth/register", json=SALMA)
    again = client.post("/api/v1/auth/register", json={**SALMA, "password": "another passphrase!"})
    assert (again.status_code, again.content) == (202, b"")
    assert login(client).status_code == 200
    assert login(client, password="another passphrase!").status_code == 401


@pytest.mark.parametrize(("email", "password"), [("salma@example.com", "wrong passphrase"),
                                                 ("nobody@example.com", PASSWORD)])  # fmt: skip
def test_bad_credentials_give_one_generic_401(client, email, password):
    client.post("/api/v1/auth/register", json=SALMA)
    response = login(client, email, password)
    assert (response.status_code, response.json()["code"]) == (401, "INVALID_CREDENTIALS")
    assert "set-cookie" not in response.headers


def test_without_a_session_me_is_401_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert (response.status_code, response.json()["code"]) == (401, "UNAUTHENTICATED")


def test_refresh_rotates_the_cookies_and_keeps_the_user_signed_in(client):
    client.post("/api/v1/auth/register", json=SALMA)
    old = login(client).cookies["replora_refresh"]
    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 204
    assert set_cookies(refreshed)["replora_refresh"]["replora_refresh"].value != old
    assert client.get("/api/v1/auth/me").status_code == 200


def test_logout_revokes_the_session_so_its_refresh_token_is_dead(client):
    client.post("/api/v1/auth/register", json=SALMA)
    login(client)
    refresh = client.cookies["replora_refresh"]
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    client.cookies.set("replora_refresh", refresh)
    response = client.post("/api/v1/auth/refresh")
    assert (response.status_code, response.json()["code"]) == (401, "UNAUTHENTICATED")


def test_a_reused_refresh_token_signs_everyone_out(client):
    client.post("/api/v1/auth/register", json=SALMA)
    login(client)
    stolen = client.cookies["replora_refresh"]
    assert client.post("/api/v1/auth/refresh").status_code == 204
    client.cookies.delete("replora_refresh")
    client.cookies.set("replora_refresh", stolen)
    assert client.post("/api/v1/auth/refresh").status_code == 401
    client.cookies.delete("replora_refresh")
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize(("env", "secure"), [("development", False), ("production", True)])
def test_session_cookies_are_httponly_lax_on_root_and_secure_in_production(db_url, env, secure):
    extra = {"openrouter_api_key": "k", "jwt_secret": "j" * 43} if env == "production" else {}
    client = app_client(db_url, app_env=env, **extra)
    client.post("/api/v1/auth/register", json=SALMA)
    cookies = set_cookies(login(client))
    for name in ("replora_access", "replora_refresh"):
        morsel = cookies[name][name]
        assert morsel["httponly"] is True
        assert (morsel["samesite"].lower(), morsel["path"]) == ("lax", "/")
        assert bool(morsel["secure"]) is secure


def test_an_access_token_of_a_revoked_session_is_refused_before_it_expires(client):
    client.post("/api/v1/auth/register", json=SALMA)
    login(client)
    access = client.cookies["replora_access"]
    client.post("/api/v1/auth/logout")
    client.cookies.delete("replora_access")
    client.cookies.set("replora_access", access)
    response = client.get("/api/v1/auth/me")
    assert (response.status_code, response.json()["code"]) == (401, "UNAUTHENTICATED")
