"""P5.11 MFA: enrollment, confirmation, recovery codes, disabling (T5.15, S-28)."""

import itertools
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from conftest import with_csrf
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.mail import Outbox
from app.auth.totp import code_at, step_of
from app.config import Settings
from app.db import models as m
from app.db.base import Base
from app.db.engine import make_engine, make_sessions
from app.main import create_app

PASSWORD = "a long and unusual passphrase"
ADDRESSES = itertools.count(1)


@pytest.fixture
def app(db_url):
    Base.metadata.create_all(make_engine(db_url))
    application = create_app(Settings(_env_file=None, database_url=db_url))
    application.state.mailer = Outbox()
    application.state.db = make_sessions(make_engine(db_url))
    application.state.at = [application.state.clock()]
    application.state.clock = lambda: application.state.at[0]
    return application


def person(app) -> TestClient:
    client = with_csrf(TestClient(app, client=(f"10.7.0.{next(ADDRESSES)}", 1)))
    body = {"email": "salma@example.com", "password": PASSWORD, "display_name": "S",
            "locale": "ar"}  # fmt: skip
    client.post("/api/v1/auth/register", json=body)
    client.post("/api/v1/auth/login", json={"email": body["email"], "password": PASSWORD})
    return client


def code(app, secret: str, ahead: int = 0) -> str:
    return code_at(secret, step_of(app.state.at[0]) + ahead)


def wrong_code(app, secret: str) -> str:
    """A code that matches none of the three steps a check accepts."""
    valid = {code(app, secret, ahead) for ahead in (-1, 0, 1)}
    return next(c for c in (f"{n:06d}" for n in range(10)) if c not in valid)


def enroll(app, client) -> tuple[str, list[str]]:
    response = client.post("/api/v1/auth/mfa/enroll")
    assert response.status_code == 200
    body = response.json()
    secret = parse_qs(urlparse(body["otpauth_uri"]).query)["secret"][0]
    return secret, body["recovery_codes"]


def enabled(app, client, secret) -> None:
    assert client.post("/api/v1/auth/mfa/enroll/confirm",
                       json={"code": code(app, secret)}).status_code == 204  # fmt: skip


def test_enrollment_gives_a_uri_and_ten_codes_but_mfa_waits_for_confirmation(app):
    client = person(app)
    secret, codes = enroll(app, client)
    assert len(codes) == 10 and len(set(codes)) == 10
    assert client.get("/api/v1/auth/me").json()["mfa_enabled"] is False
    enabled(app, client, secret)
    assert client.get("/api/v1/auth/me").json()["mfa_enabled"] is True


def test_a_wrong_confirmation_code_is_refused(app):
    client = person(app)
    secret, _ = enroll(app, client)
    response = client.post(
        "/api/v1/auth/mfa/enroll/confirm", json={"code": wrong_code(app, secret)}
    )
    assert (response.status_code, response.json()["code"]) == (400, "MFA_CODE_INVALID")


def test_the_secret_is_encrypted_and_recovery_codes_are_hashed(app):
    client = person(app)
    secret, codes = enroll(app, client)
    with app.state.db() as session:
        user = session.scalars(select(m.User)).one()
        stored = list(session.scalars(select(m.MfaRecoveryCode.code_hash)))
    assert secret.encode() not in user.mfa_secret_enc
    assert len(stored) == 10 and not set(codes) & set(stored)


def test_enrolling_twice_once_enabled_is_a_conflict(app):
    client = person(app)
    secret, _ = enroll(app, client)
    enabled(app, client, secret)
    response = client.post("/api/v1/auth/mfa/enroll")
    assert (response.status_code, response.json()["code"]) == (409, "MFA_ALREADY_ENABLED")


def test_disabling_needs_the_password_and_a_code(app):
    client = person(app)
    secret, _ = enroll(app, client)
    enabled(app, client, secret)
    app.state.at[0] += timedelta(seconds=30)
    wrong_password = {"password": "wrong passphrase!", "code": code(app, secret)}
    response = client.request("DELETE", "/api/v1/auth/mfa", json=wrong_password)
    assert response.json()["code"] == "PASSWORD_INCORRECT"
    bad_code = {"password": PASSWORD, "code": wrong_code(app, secret)}
    response = client.request("DELETE", "/api/v1/auth/mfa", json=bad_code)
    assert response.json()["code"] == "MFA_CODE_INVALID"
    good = {"password": PASSWORD, "code": code(app, secret)}
    assert client.request("DELETE", "/api/v1/auth/mfa", json=good).status_code == 204
    assert client.get("/api/v1/auth/me").json()["mfa_enabled"] is False
    with app.state.db() as session:
        assert session.scalars(select(m.MfaRecoveryCode)).all() == []


def test_disabling_when_not_enabled_is_a_conflict(app):
    client = person(app)
    response = client.request("DELETE", "/api/v1/auth/mfa", json={"password": PASSWORD,
                                                                  "code": "123456"})  # fmt: skip
    assert (response.status_code, response.json()["code"]) == (409, "MFA_NOT_ENABLED")


def mfa_user(app):
    """A signed-out client whose account has MFA on, the secret and the recovery codes."""
    client = person(app)
    secret, codes = enroll(app, client)
    enabled(app, client, secret)
    client.post("/api/v1/auth/logout")
    app.state.at[0] += timedelta(seconds=30)
    return client, secret, codes


def password_step(client):
    return client.post("/api/v1/auth/login", json={"email": "salma@example.com",
                                                   "password": PASSWORD})  # fmt: skip


def challenge(client, **body):
    return client.post("/api/v1/auth/mfa/challenge", json=body)


def cookie_names(response) -> set[str]:
    return {header.split("=")[0] for header in response.headers.get_list("set-cookie")}


def test_login_with_mfa_asks_for_a_code_and_issues_no_session(app):
    client, _, _ = mfa_user(app)
    response = password_step(client)
    assert (response.status_code, response.json()) == (200, {"mfa_required": True})
    assert "replora_mfa_challenge" in cookie_names(response)
    assert not {"replora_access", "replora_refresh"} & cookie_names(response)
    assert "httponly" in next(h for h in response.headers.get_list("set-cookie")
                              if h.startswith("replora_mfa_challenge")).lower()  # fmt: skip
    assert client.get("/api/v1/auth/me").status_code == 401


def test_the_right_code_completes_the_login(app):
    client, secret, _ = mfa_user(app)
    password_step(client)
    response = challenge(client, code=code(app, secret))
    assert (response.status_code, response.json()["mfa_enabled"]) == (200, True)
    assert {"replora_access", "replora_refresh"} <= cookie_names(response)
    assert client.get("/api/v1/auth/me").status_code == 200


def test_a_challenge_works_once(app):
    client, secret, _ = mfa_user(app)
    password_step(client)
    stolen = client.cookies["replora_mfa_challenge"]
    challenge(client, code=code(app, secret))
    client.cookies.set("replora_mfa_challenge", stolen)
    app.state.at[0] += timedelta(seconds=30)
    response = challenge(client, code=code(app, secret))
    assert (response.status_code, response.json()["code"]) == (401, "MFA_CHALLENGE_INVALID")


@pytest.mark.parametrize("case", ["expired", "missing"])
def test_an_expired_or_missing_challenge_is_refused(app, case):
    client, secret, _ = mfa_user(app)
    password_step(client)
    if case == "expired":
        app.state.at[0] += timedelta(minutes=5)
    else:
        client.cookies.delete("replora_mfa_challenge")
    response = challenge(client, code=code(app, secret))
    assert (response.status_code, response.json()["code"]) == (401, "MFA_CHALLENGE_INVALID")


def test_wrong_codes_are_throttled_with_the_login_limit(app):
    client, secret, _ = mfa_user(app)
    password_step(client)
    statuses = [challenge(client, code=wrong_code(app, secret)).status_code for _ in range(6)]
    assert statuses == [400] * 5 + [429]


def test_a_recovery_code_works_exactly_once(app):
    client, _, codes = mfa_user(app)
    password_step(client)
    assert challenge(client, recovery_code=codes[0]).status_code == 200
    client.post("/api/v1/auth/logout")
    password_step(client)
    response = challenge(client, recovery_code=codes[0])
    assert (response.status_code, response.json()["code"]) == (400, "MFA_CODE_INVALID")
    assert challenge(client, recovery_code=codes[1]).status_code == 200
