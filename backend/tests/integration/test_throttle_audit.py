"""P5.7 login throttling and lockout (T5.7, S-26) and the auth audit log (T5.12)."""

from datetime import timedelta

import pytest
from conftest import with_csrf
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.mail import Outbox
from app.config import Settings
from app.db import models as m
from app.db.base import Base
from app.db.engine import make_engine, make_sessions
from app.main import create_app

PASSWORD = "a long and unusual passphrase"
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
    client.clock, client.db = Clock(app), make_sessions(make_engine(db_url))
    client.post("/api/v1/auth/register", json=SALMA)
    return client


def login(web, password=PASSWORD, email="salma@example.com"):
    return web.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_the_sixth_failure_in_15_minutes_is_429_with_retry_after(web):
    for _ in range(5):
        assert login(web, "wrong passphrase!").status_code == 401
    response = login(web, "wrong passphrase!")
    assert (response.status_code, response.json()["code"]) == (429, "RATE_LIMITED")
    assert 0 < int(response.headers["retry-after"]) <= 15 * 60


def test_while_locked_even_the_right_password_is_refused(web):
    for _ in range(6):
        login(web, "wrong passphrase!")
    assert login(web).status_code == 429


def test_the_lockout_releases_after_the_window(web):
    for _ in range(6):
        login(web, "wrong passphrase!")
    web.clock.at += timedelta(minutes=15)
    assert login(web).status_code == 200


def test_successful_logins_do_not_count(web):
    for _ in range(8):
        assert login(web).status_code == 200


def test_failures_for_one_account_from_many_addresses_lock_that_account(web):
    for k in range(5):
        other = with_csrf(TestClient(web.app, client=(f"10.1.0.{k}", 1)))
        assert login(other, "wrong passphrase!").status_code == 401
    fresh = with_csrf(TestClient(web.app, client=("10.2.0.1", 1)))
    assert login(fresh).status_code == 429


def test_failures_on_unknown_accounts_are_throttled_per_ip(web):
    for k in range(5):
        login(web, email=f"nobody{k}@example.com")
    assert login(web, email="someone.else@example.com").status_code == 429


def test_forgot_password_is_limited_to_3_an_hour_per_ip(web):
    forgot = {"email": "x@example.com"}
    statuses = [web.post("/api/v1/auth/password/forgot", json=forgot).status_code
                for _ in range(4)]  # fmt: skip
    assert statuses == [202, 202, 202, 429]


def test_register_is_limited_to_3_an_hour_per_ip(web):
    bodies = [{**SALMA, "email": f"u{k}@example.com"} for k in range(3)]
    statuses = [web.post("/api/v1/auth/register", json=body).status_code for body in bodies]
    assert statuses == [202, 202, 429]  # the fixture's registration was the first


def actions(web) -> list[tuple[str, bool]]:
    with web.db() as session:
        rows = session.scalars(select(m.AuditEvent).order_by(m.AuditEvent.created_at)).all()
    return [(row.action, row.actor_id is not None) for row in rows]


def test_auth_events_are_audited_without_raw_emails(web):
    login(web, "wrong passphrase!")
    login(web)
    web.post("/api/v1/auth/logout")
    web.post("/api/v1/auth/password/forgot", json={"email": "salma@example.com"})
    token = web.app.state.mailer.sent[-1].body.split("token=")[1]
    web.post("/api/v1/auth/password/reset", json={"token": token, "password": PASSWORD + "!"})
    assert actions(web) == [
        ("auth.register", True), ("auth.login_failed", True), ("auth.login", True),
        ("auth.logout", True), ("auth.password_reset", True),
    ]  # fmt: skip
    with web.db() as session:
        targets = session.scalars(select(m.AuditEvent.target_id)).all()
    assert not any("@" in (target or "") for target in targets)


def test_a_failed_login_for_an_unknown_email_is_audited_with_no_actor(web):
    login(web, email="nobody@example.com")
    assert actions(web)[-1] == ("auth.login_failed", False)
