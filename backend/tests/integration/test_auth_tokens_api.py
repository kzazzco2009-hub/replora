"""P5.4 email verification and password reset (T5.3 verify part, T5.8, T5.11)."""

import re
import statistics
import time
from datetime import timedelta

import pytest
from conftest import with_csrf
from fastapi.testclient import TestClient

from app.auth.mail import Outbox
from app.config import Settings
from app.db.base import Base
from app.db.engine import make_engine
from app.main import create_app

PASSWORD = "a long and unusual passphrase"
NEW_PASSWORD = "another long new passphrase"
SALMA = {"email": "salma@example.com", "password": PASSWORD, "display_name": "S", "locale": "ar"}


class Clock:
    def __init__(self, app) -> None:
        self.at = app.state.clock()
        app.state.clock = lambda: self.at


@pytest.fixture
def web(db_url):
    Base.metadata.create_all(make_engine(db_url))
    app = create_app(Settings(_env_file=None, database_url=db_url))
    app.state.mailer = Outbox()
    client = with_csrf(TestClient(app))
    client.clock = Clock(app)
    client.outbox = app.state.mailer
    return client


def token_in(message) -> str:
    return re.search(r"token=([\w-]+)", message.body).group(1)


def login(web, password=PASSWORD):
    return web.post("/api/v1/auth/login", json={"email": SALMA["email"], "password": password})


def test_registration_sends_a_verification_link_that_verifies_the_email(web):
    web.post("/api/v1/auth/register", json=SALMA)
    (message,) = web.outbox.sent
    assert (message.to, message.kind) == ("salma@example.com", "verify")
    assert (
        web.post("/api/v1/auth/verify-email", json={"token": token_in(message)}).status_code == 204
    )
    assert login(web).json()["email_verified"] is True


def test_registering_an_existing_email_sends_a_notice_with_no_token(web):
    web.post("/api/v1/auth/register", json=SALMA)
    web.post("/api/v1/auth/register", json=SALMA)
    assert [m.kind for m in web.outbox.sent] == ["verify", "account_exists"]
    assert "token=" not in web.outbox.sent[1].body


def test_a_verification_token_works_once(web):
    web.post("/api/v1/auth/register", json=SALMA)
    token = token_in(web.outbox.sent[0])
    web.post("/api/v1/auth/verify-email", json={"token": token})
    again = web.post("/api/v1/auth/verify-email", json={"token": token})
    assert (again.status_code, again.json()["code"]) == (400, "TOKEN_INVALID")


def reset_token(web) -> str:
    web.post("/api/v1/auth/register", json=SALMA)
    assert (
        web.post("/api/v1/auth/password/forgot", json={"email": "SALMA@example.com"}).status_code
        == 202
    )
    message = web.outbox.sent[-1]
    assert message.kind == "reset"
    return token_in(message)


def test_reset_sets_the_new_password_and_revokes_every_session(web):
    token = reset_token(web)
    assert login(web).status_code == 200
    body = {"token": token, "password": NEW_PASSWORD}
    assert web.post("/api/v1/auth/password/reset", json=body).status_code == 204
    assert web.get("/api/v1/auth/me").status_code == 401
    assert login(web).status_code == 401
    assert login(web, NEW_PASSWORD).status_code == 200


def test_a_reset_token_works_once(web):
    token = reset_token(web)
    web.post("/api/v1/auth/password/reset", json={"token": token, "password": NEW_PASSWORD})
    again = web.post("/api/v1/auth/password/reset", json={"token": token, "password": PASSWORD})
    assert (again.status_code, again.json()["code"]) == (400, "TOKEN_INVALID")


@pytest.mark.parametrize(("minutes", "status"), [(29, 204), (30, 400)])
def test_a_reset_token_expires_after_30_minutes(web, minutes, status):
    token = reset_token(web)
    web.clock.at += timedelta(minutes=minutes)
    body = {"token": token, "password": NEW_PASSWORD}
    assert web.post("/api/v1/auth/password/reset", json=body).status_code == status


def test_a_verify_token_does_not_reset_a_password(web):
    web.post("/api/v1/auth/register", json=SALMA)
    body = {"token": token_in(web.outbox.sent[0]), "password": NEW_PASSWORD}
    assert web.post("/api/v1/auth/password/reset", json=body).status_code == 400


def test_forgot_password_answers_the_same_for_known_and_unknown_emails(web):
    web.post("/api/v1/auth/register", json=SALMA)
    sent = len(web.outbox.sent)
    timings, answers = {}, {}
    for email in ("salma@example.com", "nobody@example.com"):
        samples = []
        for k in range(5):
            # A fresh address each time, so the 3-per-hour limit doesn't answer instead.
            client = with_csrf(TestClient(web.app, client=(f"10.9.{len(email)}.{k}", 1)))
            start = time.perf_counter()
            response = client.post("/api/v1/auth/password/forgot", json={"email": email})
            samples.append(time.perf_counter() - start)
            answers[email] = (response.status_code, response.content)
        timings[email] = statistics.median(samples)
    assert answers["salma@example.com"] == answers["nobody@example.com"] == (202, b"")
    assert len(web.outbox.sent) == sent + 5
    assert abs(timings["salma@example.com"] - timings["nobody@example.com"]) < 0.05
