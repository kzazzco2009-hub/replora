"""A signed-in browser client on a fresh database, and the upload flow, for the API tests."""

import itertools
import json
from uuid import uuid4

from conftest import with_csrf
from fastapi.testclient import TestClient

from app.auth.mail import Outbox
from app.config import Settings
from app.db.base import Base
from app.db.engine import make_engine
from app.main import create_app
from app.worker import work_once

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


ORDERS = b"order_id,amount\nO-101,100\nO-102,200\nO-103,300\n"
PAYMENTS = json.dumps([{"order_id": "O-101", "amount": 100}, {"order_id": "O-102", "amount": 190},
                       {"order_id": "O-104", "amount": 50}]).encode()  # fmt: skip


def reconciled(client: TestClient) -> dict:
    """The Phase 7 files reconciled end to end: draft, run, approve, then the worker to the end."""
    ids = [
        upload(client, "orders.csv", ORDERS)["id"],
        upload(client, "payments.json", PAYMENTS)["id"],
    ]
    body = {"file_ids": ids, "planner": "template", "template_id": "reconcile"}
    draft = client.post(f"/api/v1/workspaces/{client.ws}/drafts", json=body).json()
    runs = f"/api/v1/workspaces/{client.ws}/runs"
    run = client.post(runs, json={"draft_id": draft["id"]},
                      headers={"Idempotency-Key": str(uuid4())}).json()  # fmt: skip
    client.post(f"{runs}/{run['id']}/approve", json={"plan_hash": run["plan_hash"]},
                headers={"Idempotency-Key": str(uuid4())})  # fmt: skip
    while work_once(client.app.state.sessions, client.app.state.storage):
        pass
    return client.get(f"{runs}/{run['id']}").json()
