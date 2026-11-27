"""P5.10 account deletion with a grace period, and data export (T5.14, S-29)."""

import io
import itertools
import json
import zipfile
from datetime import timedelta
from uuid import UUID

import pytest
from conftest import with_csrf
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.mail import Outbox
from app.auth.privacy import purge_deleted
from app.config import Settings
from app.db import models as m
from app.db.base import Base
from app.db.engine import make_engine, make_sessions
from app.main import create_app

PASSWORD = "a long and unusual passphrase"
ADDRESSES = itertools.count(1)


@pytest.fixture
def app(db_url, tmp_path):
    Base.metadata.create_all(make_engine(db_url))
    application = create_app(Settings(_env_file=None, database_url=db_url, data_dir=tmp_path))
    application.state.mailer = Outbox()
    application.state.db = make_sessions(make_engine(db_url))
    return application


def person(app, name: str) -> TestClient:
    client = with_csrf(TestClient(app, client=(f"10.6.0.{next(ADDRESSES)}", 1)))
    email = f"{name}@example.com"
    body = {"email": email, "password": PASSWORD, "display_name": name, "locale": "en"}
    client.post("/api/v1/auth/register", json=body)
    client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    me = client.get("/api/v1/auth/me").json()
    client.user_id, client.personal = me["id"], me["memberships"][0]["id"]
    with app.state.db.begin() as session:
        session.add(m.Workflow(workspace_id=UUID(client.personal), name=f"{name}'s workflow"))
    return client


def test_the_export_holds_only_the_users_own_data(app):
    other, salma = person(app, "other"), person(app, "salma")
    started = salma.post("/api/v1/auth/me/export")
    assert started.status_code == 202
    export_id = started.json()["export_id"]
    status = salma.get(f"/api/v1/auth/me/export/{export_id}").json()
    assert status["status"] == "ready"
    download = salma.get(status["url"])
    assert "replora-export.zip" in download.headers["content-disposition"]
    data = download.content
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = set(archive.namelist())
        everything = b"".join(archive.read(name) for name in names)
        profile = json.loads(archive.read("profile.json"))
    assert {"profile.json", "workspaces.json", "workflows.json", "runs.json"} <= names
    assert profile["email"] == "salma@example.com"
    assert b"salma's workflow" in everything
    assert b"other" not in everything and other.user_id.encode() not in everything
    assert b"password_hash" not in everything and b"$argon2" not in everything


def test_another_users_export_is_not_found(app):
    salma, other = person(app, "salma"), person(app, "other")
    export_id = salma.post("/api/v1/auth/me/export").json()["export_id"]
    assert other.get(f"/api/v1/auth/me/export/{export_id}").status_code == 404


def test_deletion_needs_the_password(app):
    salma = person(app, "salma")
    response = salma.request("DELETE", "/api/v1/auth/me", json={"password": "wrong passphrase!"})
    assert (response.status_code, response.json()["code"]) == (400, "PASSWORD_INCORRECT")


def test_after_deletion_the_user_cannot_sign_in_and_sessions_end(app):
    salma = person(app, "salma")
    assert (
        salma.request("DELETE", "/api/v1/auth/me", json={"password": PASSWORD}).status_code == 202
    )
    assert salma.get("/api/v1/auth/me").status_code == 401
    login = salma.post("/api/v1/auth/login",
                       json={"email": "salma@example.com", "password": PASSWORD})  # fmt: skip
    assert login.status_code == 401
    with app.state.db() as session:
        rows = session.scalars(select(m.Session).where(m.Session.user_id == UUID(salma.user_id)))
        assert all(row.revoked_at is not None for row in rows)


def test_the_purge_waits_for_the_grace_period_then_removes_the_user_and_anonymizes_audit(app):
    salma = person(app, "salma")
    salma.request("DELETE", "/api/v1/auth/me", json={"password": PASSWORD})
    grace = app.state.settings.deletion_grace
    deleted_at = app.state.clock()
    stored = f"{salma.personal}/kept-file"
    app.state.storage.put(stored, b"x")
    with app.state.db.begin() as session:
        session.add(
            m.File(
                workspace_id=UUID(salma.personal),
                storage_key=stored,
                display_name="x",
                size=1,
                status="ready",
            )
        )
    with app.state.db.begin() as session:
        assert (
            purge_deleted(
                session, app.state.storage, deleted_at + grace - timedelta(seconds=1), grace
            )
            == 0
        )
    with app.state.db.begin() as session:
        assert purge_deleted(session, app.state.storage, deleted_at + grace, grace) == 1
    assert not app.state.storage.exists(stored)
    with app.state.db() as session:
        assert session.get(m.User, UUID(salma.user_id)) is None
        assert session.get(m.Workspace, UUID(salma.personal)) is None
        assert session.scalars(select(m.Workflow)).all() == []
        events = session.scalars(select(m.AuditEvent)).all()
    assert events and all(event.actor_id is None for event in events)


def test_an_owner_of_a_shared_workspace_must_hand_it_over_first(app):
    salma = person(app, "salma")
    salma.post("/api/v1/workspaces", json={"name": "Team"})
    response = salma.request("DELETE", "/api/v1/auth/me", json={"password": PASSWORD})
    assert (response.status_code, response.json()["code"]) == (409, "OWNS_SHARED_WORKSPACE")
    assert salma.get("/api/v1/auth/me").status_code == 200
