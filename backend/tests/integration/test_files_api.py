"""P6.2 and P6.3 the upload flow: intent → PUT → complete (T6.2, T6.7, T6.8, S-31, S-34)."""

import hashlib
import itertools

import pytest
from conftest import with_csrf
from fastapi.testclient import TestClient

from app.auth.mail import Outbox
from app.config import Settings
from app.db.base import Base
from app.db.engine import make_engine
from app.main import create_app

PASSWORD = "a long and unusual passphrase"
MiB = 1024 * 1024
CSV = b"order_id,amount\nA1,10\n"
ADDRESSES = itertools.count(1)


@pytest.fixture
def web(db_url, tmp_path):
    Base.metadata.create_all(make_engine(db_url))
    app = create_app(Settings(_env_file=None, database_url=db_url, data_dir=tmp_path))
    app.state.mailer = Outbox()
    client = with_csrf(TestClient(app, client=(f"10.8.0.{next(ADDRESSES)}", 1)))
    body = {"email": "s@example.com", "password": PASSWORD, "display_name": "S", "locale": "en"}
    client.post("/api/v1/auth/register", json=body)
    client.post("/api/v1/auth/login", json={"email": body["email"], "password": PASSWORD})
    client.ws = client.get("/api/v1/auth/me").json()["memberships"][0]["id"]
    return client


def intent(web, size, name="orders.csv"):
    body = {"display_name": name, "size": size, "content_type": "text/csv"}
    return web.post(f"/api/v1/workspaces/{web.ws}/files/upload-intent", json=body)


def upload(web, data: bytes, declared: int | None = None, name="orders.csv"):
    created = intent(web, len(data) if declared is None else declared, name).json()
    target = created["upload"]
    assert web.request(target["method"], target["url"], content=data,
                       headers=target["headers"]).status_code == 200  # fmt: skip
    return web.post(f"/api/v1/workspaces/{web.ws}/files/{created['file_id']}/complete")


def test_the_full_flow_gives_a_ready_file_with_the_servers_hash(web):
    response = upload(web, CSV)
    assert response.status_code == 200
    file = response.json()
    assert (file["status"], file["detected_type"], file["size"]) == ("ready", "csv", len(CSV))
    assert file["sha256"] == hashlib.sha256(CSV).hexdigest()
    assert file["display_name"] == "orders.csv"


def test_an_intent_is_pending_and_gives_a_10_minute_put(web):
    created = intent(web, 10)
    assert created.status_code == 201
    upload_target = created.json()["upload"]
    assert upload_target["method"] == "PUT" and upload_target["url"].startswith("/api/v1/storage/")
    file_id = created.json()["file_id"]
    assert web.get(f"/api/v1/workspaces/{web.ws}/files/{file_id}").json()["status"] == "pending"


@pytest.mark.parametrize(("size", "status"), [(50 * MiB, 201), (50 * MiB + 1, 413)])
def test_the_declared_size_is_checked_at_intent(web, size, status):
    response = intent(web, size)
    assert response.status_code == status
    if status == 413:
        assert response.json()["code"] == "FILE_TOO_LARGE"


def test_a_size_mismatch_is_rejected_and_the_bytes_removed(web):
    response = upload(web, CSV, declared=len(CSV) + 5)
    file = response.json()
    assert (file["status"], file["rejection_code"]) == ("rejected", "FILE_SIZE_MISMATCH")
    assert not web.app.state.storage.exists(f"{web.ws}/{file['id']}")


@pytest.mark.parametrize(("data", "name", "code"), [
    (b"MZ\x90\x00" + b"\x00" * 60, "invoice.csv", "FILE_TYPE_UNSUPPORTED"),
    (b"<html><script>x</script></html>", "photo.png", "FILE_TYPE_UNSUPPORTED"),
])  # fmt: skip
def test_a_renamed_file_is_rejected_by_its_content(web, data, name, code):
    file = upload(web, data, name=name).json()
    assert (file["status"], file["rejection_code"]) == ("rejected", code)


def test_complete_without_any_upload_is_an_empty_file(web):
    file_id = intent(web, 10).json()["file_id"]
    file = web.post(f"/api/v1/workspaces/{web.ws}/files/{file_id}/complete").json()
    assert (file["status"], file["rejection_code"]) == ("rejected", "FILE_EMPTY")


def test_the_display_name_is_sanitized(web):
    file = upload(web, CSV, name="../../x‮evil.csv").json()
    assert file["display_name"] == "xevil.csv"


def test_a_completed_file_cannot_be_completed_again(web):
    file = upload(web, CSV).json()
    again = web.post(f"/api/v1/workspaces/{web.ws}/files/{file['id']}/complete")
    assert (again.status_code, again.json()["code"]) == (409, "INVALID_STATE_TRANSITION")
