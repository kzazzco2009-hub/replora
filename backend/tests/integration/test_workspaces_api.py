"""P5.8 profile, sessions, workspaces and member management."""

import itertools
from uuid import UUID

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
ADDRESSES = itertools.count(1)


@pytest.fixture
def app(db_url):
    Base.metadata.create_all(make_engine(db_url))
    application = create_app(Settings(_env_file=None, database_url=db_url))
    application.state.mailer = Outbox()
    application.state.db_url = db_url
    return application


def person(app, name: str) -> TestClient:
    client = with_csrf(TestClient(app, client=(f"10.3.0.{next(ADDRESSES)}", 1)))
    body = {"email": f"{name}@example.com", "password": PASSWORD, "display_name": name,
            "locale": "en"}  # fmt: skip
    client.post("/api/v1/auth/register", json=body)
    client.post("/api/v1/auth/login", json={"email": body["email"], "password": PASSWORD})
    client.user_id = client.get("/api/v1/auth/me").json()["id"]
    return client


def add_member(app, ws: str, client: TestClient, role: str) -> None:
    with make_sessions(make_engine(app.state.db_url)).begin() as session:
        session.add(m.Membership(workspace_id=UUID(ws), user_id=UUID(client.user_id), role=role))


def audit(app) -> list[str]:
    with make_sessions(make_engine(app.state.db_url))() as session:
        return list(session.scalars(select(m.AuditEvent.action).order_by(m.AuditEvent.created_at)))


def test_workspaces_list_mine_and_a_new_one_is_owned_by_its_creator(app):
    owner = person(app, "owner")
    created = owner.post("/api/v1/workspaces", json={"name": "Finance"})
    assert created.status_code == 201
    assert (created.json()["name"], created.json()["role"]) == ("Finance", "owner")
    names = [w["name"] for w in owner.get("/api/v1/workspaces").json()]
    assert names == ["owner", "Finance"]
    assert "workspace.created" in audit(app)


def test_the_personal_workspace_cannot_be_deleted_but_another_can(app):
    owner = person(app, "owner")
    personal = owner.get("/api/v1/workspaces").json()[0]["id"]
    response = owner.delete(f"/api/v1/workspaces/{personal}")
    assert (response.status_code, response.json()["code"]) == (
        409,
        "PERSONAL_WORKSPACE_UNDELETABLE",
    )
    other = owner.post("/api/v1/workspaces", json={"name": "Temp"}).json()["id"]
    assert owner.delete(f"/api/v1/workspaces/{other}").status_code == 204
    assert owner.get(f"/api/v1/workspaces/{other}/members").status_code == 404


def team(app):
    owner, admin, member = person(app, "owner"), person(app, "admin"), person(app, "member")
    ws = owner.post("/api/v1/workspaces", json={"name": "Team"}).json()["id"]
    add_member(app, ws, admin, "admin")
    add_member(app, ws, member, "member")
    return ws, owner, admin, member


def test_members_are_listed_with_their_roles(app):
    ws, owner, _, member = team(app)
    rows = member.get(f"/api/v1/workspaces/{ws}/members").json()
    assert {(r["display_name"], r["role"]) for r in rows} == {
        ("owner", "owner"), ("admin", "admin"), ("member", "member")}  # fmt: skip


def test_a_manager_changes_a_role_and_it_is_audited(app):
    ws, owner, admin, member = team(app)
    url = f"/api/v1/workspaces/{ws}/members/{member.user_id}"
    response = admin.patch(url, json={"role": "viewer"})
    assert (response.status_code, response.json()["role"]) == (200, "viewer")
    assert "member.role_changed" in audit(app)
    assert member.post(f"/api/v1/workspaces/{ws}/files/upload-intent", json={}).status_code == 403


@pytest.mark.parametrize("who", ["owner", "admin-on-admin"])
def test_the_owner_and_peers_are_protected_from_managers(app, who):
    ws, owner, admin, member = team(app)
    other_admin = person(app, "admin2")
    add_member(app, ws, other_admin, "admin")
    target = owner if who == "owner" else other_admin
    url = f"/api/v1/workspaces/{ws}/members/{target.user_id}"
    for response in (admin.patch(url, json={"role": "viewer"}), admin.delete(url)):
        assert (response.status_code, response.json()["code"]) == (403, "PERMISSION_DENIED")


def test_the_owner_can_remove_a_member_who_then_loses_access(app):
    ws, owner, _, member = team(app)
    assert owner.delete(f"/api/v1/workspaces/{ws}/members/{member.user_id}").status_code == 204
    assert member.get(f"/api/v1/workspaces/{ws}/members").status_code == 404
    assert "member.removed" in audit(app)


def test_a_member_not_in_the_workspace_is_not_found(app):
    ws, owner, _, _ = team(app)
    stranger = person(app, "stranger")
    url = f"/api/v1/workspaces/{ws}/members/{stranger.user_id}"
    assert owner.patch(url, json={"role": "viewer"}).status_code == 404


def test_the_profile_can_be_updated(app):
    owner = person(app, "owner")
    body = {"display_name": "سلمى", "locale": "ar", "theme": "dark", "timezone": "Africa/Cairo"}
    response = owner.patch("/api/v1/auth/me", json=body)
    assert response.status_code == 200
    assert {k: response.json()[k] for k in body} == body


def test_an_unknown_timezone_is_refused(app):
    response = person(app, "owner").patch("/api/v1/auth/me", json={"timezone": "Mars/Olympus"})
    assert (response.status_code, response.json()["errors"][0]["path"]) == (422, "body.timezone")


def test_sessions_are_listed_and_another_one_can_be_revoked(app):
    owner = person(app, "owner")
    laptop = with_csrf(TestClient(app, client=("10.4.0.1", 1)))
    laptop.post("/api/v1/auth/login", json={"email": "owner@example.com", "password": PASSWORD})
    listed = owner.get("/api/v1/auth/sessions").json()
    assert sorted(s["current"] for s in listed) == [False, True]
    other = next(s["id"] for s in listed if not s["current"])
    assert owner.delete(f"/api/v1/auth/sessions/{other}").status_code == 204
    assert laptop.get("/api/v1/auth/me").status_code == 401
    assert len(owner.get("/api/v1/auth/sessions").json()) == 1


def test_revoking_the_current_session_signs_out(app):
    owner = person(app, "owner")
    (current,) = owner.get("/api/v1/auth/sessions").json()
    assert owner.delete(f"/api/v1/auth/sessions/{current['id']}").status_code == 204
    assert owner.get("/api/v1/auth/me").status_code == 401


def test_someone_elses_session_is_not_found(app):
    owner, other = person(app, "owner"), person(app, "other")
    (theirs,) = other.get("/api/v1/auth/sessions").json()
    assert owner.delete(f"/api/v1/auth/sessions/{theirs['id']}").status_code == 404


def test_the_owner_cannot_demote_or_remove_themselves(app):
    ws, owner, _, _ = team(app)
    url = f"/api/v1/workspaces/{ws}/members/{owner.user_id}"
    assert owner.patch(url, json={"role": "admin"}).status_code == 403
    assert owner.delete(url).status_code == 403
