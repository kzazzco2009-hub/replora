"""A signed-in browser client on a fresh database, and the upload flow, for the API tests."""

import itertools

from conftest import with_csrf
from fastapi.testclient import TestClient

from app.auth.mail import Outbox
from app.config import Settings
from app.db.base import Base
from app.db.engine import make_engine
from app.main import create_app

PASSWORD = "a long and unusual passphrase"
ADDRESSES = itertools.count(1)


def signed_in(db_url: str, data_dir, email: str = "s@example.com") -> TestClient:
    """Registered, signed in, with `client.ws` set to the personal workspace."""
    Base.metadata.create_all(make_engine(db_url))
    app = create_app(Settings(_env_file=None, database_url=db_url, data_dir=data_dir))
    app.state.mailer = Outbox()
    client = with_csrf(TestClient(app, client=(f"10.9.0.{next(ADDRESSES)}", 1)))
    body = {"email": email, "password": PASSWORD, "display_name": "S", "locale": "en"}
    client.post("/api/v1/auth/register", json=body)
    client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    client.ws = client.get("/api/v1/auth/me").json()["memberships"][0]["id"]
    return client


def upload(client: TestClient, name: str, data: bytes) -> dict:
    """Intent, PUT and complete: the `File` the server answers."""
    body = {"display_name": name, "size": len(data), "content_type": "application/octet-stream"}
    created = client.post(f"/api/v1/workspaces/{client.ws}/files/upload-intent", json=body).json()
    target = created["upload"]
    client.request(target["method"], target["url"], content=data, headers=target["headers"])
    return client.post(f"/api/v1/workspaces/{client.ws}/files/{created['file_id']}/complete").json()
