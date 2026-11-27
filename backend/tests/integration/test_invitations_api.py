"""P5.9 invitations (T5.13, S-29)."""

import itertools
import re
from datetime import timedelta
from typing import get_args
from uuid import UUID

import pytest
from conftest import with_csrf
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.v1.workspace_models import GrantableRole
from app.auth.mail import Outbox
from app.auth.permissions import MATRIX, Permission, Rank, Role
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
    now = application.state.clock()
    application.state.at = [now]
    application.state.clock = lambda: application.state.at[0]
    return application


def person(app, name: str, register: bool = True) -> TestClient:
    client = with_csrf(TestClient(app, client=(f"10.5.0.{next(ADDRESSES)}", 1)))
    email = f"{name}@example.com"
    if register:
        body = {"email": email, "password": PASSWORD, "display_name": name, "locale": "en"}
        client.post("/api/v1/auth/register", json=body)
        client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    return client


def workspace(app, owner) -> str:
    return owner.post("/api/v1/workspaces", json={"name": "Team"}).json()["id"]


def invite(app, client, ws, email="guest@example.com", role="member"):
    return client.post(f"/api/v1/workspaces/{ws}/invitations", json={"email": email, "role": role})


def last_token(app) -> str:
    message = app.state.mailer.sent[-1]
    assert message.kind == "invite"
    return re.search(r"token=([\w-]+)", message.body).group(1)


def accept(client, token):
    return client.post("/api/v1/invitations/accept", json={"token": token})


def test_an_existing_user_accepts_and_joins_with_the_invited_role(app):
    owner, guest = person(app, "owner"), person(app, "guest")
    ws = workspace(app, owner)
    created = invite(app, owner, ws, role="viewer")
    assert created.status_code == 201
    assert (created.json()["status"], created.json()["role"]) == ("pending", "viewer")
    joined = accept(guest, last_token(app))
    assert (joined.status_code, joined.json()["id"], joined.json()["role"]) == (200, ws, "viewer")
    roles = {
        r["display_name"]: r["role"] for r in owner.get(f"/api/v1/workspaces/{ws}/members").json()
    }
    assert roles == {"owner": "owner", "guest": "viewer"}
    assert owner.get(f"/api/v1/workspaces/{ws}/invitations").json()[0]["status"] == "accepted"


def test_a_new_sign_up_accepts_after_registering_with_the_invited_email(app):
    owner = person(app, "owner")
    ws = workspace(app, owner)
    invite(app, owner, ws, email="newcomer@example.com")
    token = last_token(app)
    newcomer = person(app, "newcomer")
    assert accept(newcomer, token).status_code == 200


@pytest.mark.parametrize("case", ["expired", "revoked", "reused", "unknown"])
def test_a_dead_token_is_refused(app, case):
    owner, guest = person(app, "owner"), person(app, "guest")
    ws = workspace(app, owner)
    invitation = invite(app, owner, ws).json()
    token = last_token(app)
    if case == "expired":
        app.state.at[0] += timedelta(days=7)
        guest.post("/api/v1/auth/login", json={"email": "guest@example.com", "password": PASSWORD})
    if case == "revoked":
        url = f"/api/v1/workspaces/{ws}/invitations/{invitation['id']}"
        assert owner.delete(url).status_code == 204
    if case == "reused":
        accept(guest, token)
    response = accept(guest, "nope" if case == "unknown" else token)
    assert (response.status_code, response.json()["code"]) == (400, "TOKEN_INVALID")


def test_an_invitation_for_x_cannot_be_accepted_by_y(app):
    owner, other = person(app, "owner"), person(app, "other")
    ws = workspace(app, owner)
    invite(app, owner, ws, email="guest@example.com")
    response = accept(other, last_token(app))
    assert (response.status_code, response.json()["code"]) == (403, "PERMISSION_DENIED")
    assert other.get(f"/api/v1/workspaces/{ws}/members").status_code == 404


def test_an_admin_cannot_invite_above_their_role_and_owner_is_never_grantable(app):
    owner, admin = person(app, "owner"), person(app, "admin")
    ws = workspace(app, owner)
    with app.state.db.begin() as session:
        user = session.scalars(select(m.User).where(m.User.email == "admin@example.com")).one()
        session.add(m.Membership(workspace_id=UUID(ws), user_id=user.id, role="admin"))
    assert invite(app, admin, ws, role="admin").status_code == 201
    assert invite(app, admin, ws, role="owner").status_code == 422


def test_invitations_store_only_a_hash_and_are_audited(app):
    owner = person(app, "owner")
    ws = workspace(app, owner)
    invite(app, owner, ws)
    token = last_token(app)
    with app.state.db() as session:
        row = session.scalars(select(m.Invitation)).one()
        actions = list(session.scalars(select(m.AuditEvent.action)))
    assert token not in row.token_hash and len(row.token_hash) == 64
    assert row.expires_at - app.state.at[0] == timedelta(days=7)
    assert "member.invited" in actions


def test_a_viewer_cannot_invite(app):
    owner, viewer = person(app, "owner"), person(app, "viewer")
    ws = workspace(app, owner)
    invite(app, owner, ws, email="viewer@example.com", role="viewer")
    accept(viewer, last_token(app))
    assert invite(app, viewer, ws).status_code == 403


def test_nobody_can_invite_above_their_own_role():
    grantable = max(Rank[Role(role).name] for role in get_args(GrantableRole))
    managers = MATRIX[Permission.MEMBERS_MANAGE]
    assert all(Rank[role.name] >= grantable for role in managers)
