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
