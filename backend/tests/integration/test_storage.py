"""P6.1 storage: LocalStorage, signed single-purpose URLs, and the local upload/download routes."""

from datetime import UTC, datetime, timedelta
from uuid import uuid7

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.base import Base
from app.db.engine import make_engine
from app.main import create_app
from app.storage.local import LocalStorage
from app.storage.signing import sign, verify

KEY = "k" * 43
NOW = datetime(2026, 11, 27, 12, tzinfo=UTC)


def test_a_signed_token_carries_its_claims_until_it_expires():
    token = sign({"op": "put", "key": "w/f"}, KEY, NOW + timedelta(minutes=10))
    assert verify(token, KEY, NOW, op="put") == {"op": "put", "key": "w/f"}
    assert verify(token, KEY, NOW + timedelta(minutes=10), op="put") is None


@pytest.mark.parametrize("tamper", ["other key", "other op", "edited", "garbage"])
def test_a_token_is_refused_when_forged_or_misused(tamper):
    token = sign({"op": "get", "key": "w/f"}, KEY, NOW + timedelta(minutes=5))
    if tamper == "edited":
        token = token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1]
    key = "x" * 43 if tamper == "other key" else KEY
    op = "put" if tamper == "other op" else "get"
    assert verify("nope" if tamper == "garbage" else token, key, NOW, op=op) is None


def test_local_storage_puts_opens_and_deletes_under_its_root(tmp_path):
    storage = LocalStorage(tmp_path, KEY)
    storage.put("ws/file", b"hello")
    assert storage.open("ws/file") == b"hello"
    assert (tmp_path / "ws" / "file").read_bytes() == b"hello"
    storage.delete("ws/file")
    assert not storage.exists("ws/file")


@pytest.mark.parametrize("key", ["../escape", "/abs", "ws/../../x", "ws\\..\\x", ""])
def test_keys_never_leave_the_root(tmp_path, key):
    with pytest.raises(ValueError):
        LocalStorage(tmp_path, KEY).put(key, b"x")


def test_upload_urls_are_short_lived_and_single_purpose(tmp_path):
    target = LocalStorage(tmp_path, KEY).create_upload_url("ws/f", 5, NOW)
    assert (target.method, target.expires_at) == ("PUT", NOW + timedelta(minutes=10))
    assert target.url.startswith("/api/v1/storage/")


@pytest.fixture
def web(db_url, tmp_path):
    Base.metadata.create_all(make_engine(db_url))
    app = create_app(Settings(_env_file=None, database_url=db_url, data_dir=tmp_path))
    return TestClient(app), app.state.storage, app


def test_the_local_put_route_stores_exactly_the_declared_bytes(web):
    client, storage, app = web
    key = f"{uuid7()}/{uuid7()}"
    target = storage.create_upload_url(key, 5, app.state.clock())
    assert client.put(target.url, content=b"hello", headers=target.headers).status_code == 200
    assert storage.open(key) == b"hello"


def test_the_put_route_refuses_more_bytes_than_declared(web):
    client, storage, app = web
    target = storage.create_upload_url("w/f", 3, app.state.clock())
    response = client.put(target.url, content=b"hello", headers=target.headers)
    assert (response.status_code, response.json()["code"]) == (413, "FILE_TOO_LARGE")
    assert not storage.exists("w/f")


def test_a_forged_or_expired_url_is_refused(web):
    client, storage, app = web
    target = storage.create_upload_url("w/f", 5, app.state.clock() - timedelta(minutes=11))
    assert client.put(target.url, content=b"hello").status_code == 403
    assert client.put("/api/v1/storage/forged", content=b"hello").status_code == 403


def test_a_download_url_serves_an_attachment_and_expires(web):
    client, storage, app = web
    storage.put("w/f", b"a,b\n1,2\n")
    now = app.state.clock()
    url, expires = storage.signed_download_url("w/f", "report.csv", now)
    assert expires - now == timedelta(minutes=5)
    response = client.get(url)
    assert (response.status_code, response.content) == (200, b"a,b\n1,2\n")
    assert response.headers["content-disposition"].startswith("attachment;")
    assert response.headers["x-content-type-options"] == "nosniff"
    app.state.clock = lambda: expires
    assert client.get(url).status_code == 403


def test_the_storage_routes_are_not_part_of_the_api_contract(web):
    client, _, _ = web
    assert not [p for p in client.get("/openapi.json").json()["paths"] if "/storage" in p]
