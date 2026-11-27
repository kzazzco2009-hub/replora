"""P6.2 and P6.3 the upload flow: intent → PUT → complete (T6.2, T6.7, T6.8, S-31, S-34)."""

import hashlib
import itertools
from uuid import UUID

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


def test_a_zip_is_ready_with_its_members_or_rejected_for_its_contents(web):
    import io
    import zipfile

    def archive(members):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as handle:
            for name, data in members.items():
                handle.writestr(name, data)
        return buffer.getvalue()

    good = upload(web, archive({"orders.csv": CSV}), name="bundle.zip").json()
    assert (good["status"], good["detected_type"]) == ("ready", "zip")
    assert good["members"] == [{"path": "orders.csv", "detected_type": "csv", "size": len(CSV)}]
    bad = upload(web, archive({"../evil.csv": CSV}), name="bundle.zip").json()
    assert (bad["status"], bad["rejection_code"]) == ("rejected", "ZIP_UNSAFE_PATH")


def test_files_are_listed_newest_first_in_pages(web):
    names = [upload(web, CSV, name=f"f{k}.csv").json()["display_name"] for k in range(3)]
    first = web.get(f"/api/v1/workspaces/{web.ws}/files", params={"limit": 2}).json()
    assert [f["display_name"] for f in first["items"]] == names[::-1][:2]
    rest = web.get(f"/api/v1/workspaces/{web.ws}/files",
                   params={"limit": 2, "cursor": first["next_cursor"]}).json()  # fmt: skip
    assert ([f["display_name"] for f in rest["items"]], rest["next_cursor"]) == ([names[0]], None)


def test_the_list_filters_by_type(web):
    upload(web, CSV)
    upload(web, b'[{"a": 1}]', name="x.json")
    listed = web.get(f"/api/v1/workspaces/{web.ws}/files", params={"type": "json"}).json()
    assert [f["detected_type"] for f in listed["items"]] == ["json"]


def test_a_bad_cursor_is_a_validation_error(web):
    response = web.get(f"/api/v1/workspaces/{web.ws}/files", params={"cursor": "nope"})
    assert response.status_code == 422


def test_a_ready_file_downloads_through_a_short_signed_link(web):
    file = upload(web, CSV).json()
    link = web.get(f"/api/v1/workspaces/{web.ws}/files/{file['id']}/download")
    assert link.status_code == 200
    downloaded = web.get(link.json()["url"])
    assert (downloaded.status_code, downloaded.content) == (200, CSV)
    assert "orders.csv" in downloaded.headers["content-disposition"]


def test_a_rejected_file_has_nothing_to_download(web):
    file = upload(web, b"MZ\x90\x00" + b"\x00" * 60).json()
    response = web.get(f"/api/v1/workspaces/{web.ws}/files/{file['id']}/download")
    assert (response.status_code, response.json()["code"]) == (409, "INVALID_STATE_TRANSITION")


def test_delete_removes_the_row_and_the_bytes(web):
    file = upload(web, CSV).json()
    assert web.delete(f"/api/v1/workspaces/{web.ws}/files/{file['id']}").status_code == 204
    assert web.get(f"/api/v1/workspaces/{web.ws}/files/{file['id']}").status_code == 404
    assert not web.app.state.storage.exists(f"{web.ws}/{file['id']}")


def test_the_samples_are_the_acceptance_files_ready_to_use(web):
    response = web.post(f"/api/v1/workspaces/{web.ws}/files/samples")
    assert response.status_code == 201
    files = {f["display_name"]: f for f in response.json()}
    assert set(files) == {"orders.csv", "payments.json"}
    assert {(f["status"], f["detected_type"]) for f in files.values()} == {
        ("ready", "csv"), ("ready", "json")}  # fmt: skip


def test_another_workspaces_file_is_not_found_from_mine(web):
    file = upload(web, CSV).json()
    other = web.post("/api/v1/workspaces", json={"name": "Other"}).json()["id"]
    assert web.get(f"/api/v1/workspaces/{other}/files/{file['id']}").status_code == 404


def test_the_retention_job_deletes_expired_files_from_the_db_and_storage(web):
    from datetime import timedelta

    from app.files.service import INPUT_RETENTION, purge_expired

    kept, gone = upload(web, CSV).json(), upload(web, CSV, name="old.csv").json()
    app = web.app
    with app.state.sessions.begin() as session:
        from app.db import models as m

        session.get(m.File, UUID(gone["id"])).expires_at = app.state.clock() - timedelta(seconds=1)
    with app.state.sessions.begin() as session:
        assert purge_expired(session, app.state.storage, app.state.clock()) == 1
    assert web.get(f"/api/v1/workspaces/{web.ws}/files/{gone['id']}").status_code == 404
    assert not app.state.storage.exists(f"{web.ws}/{gone['id']}")
    assert web.get(f"/api/v1/workspaces/{web.ws}/files/{kept['id']}").status_code == 200
    assert timedelta(days=30) == INPUT_RETENTION


def test_the_workspace_quota_blocks_new_upload_intents(db_url, tmp_path):
    Base.metadata.create_all(make_engine(db_url))
    app = create_app(Settings(_env_file=None, database_url=db_url, data_dir=tmp_path,
                              workspace_quota_bytes=len(CSV) * 2))  # fmt: skip
    app.state.mailer = Outbox()
    client = with_csrf(TestClient(app, client=("10.8.9.9", 1)))
    body = {"email": "q@example.com", "password": PASSWORD, "display_name": "Q", "locale": "en"}
    client.post("/api/v1/auth/register", json=body)
    client.post("/api/v1/auth/login", json={"email": body["email"], "password": PASSWORD})
    client.ws = client.get("/api/v1/auth/me").json()["memberships"][0]["id"]
    junk = b"MZ" + b"\x00" * (len(CSV) * 2 - 2)
    assert upload(client, junk).json()["status"] == "rejected"  # rejected bytes don't count
    assert upload(client, CSV).json()["status"] == "ready"
    assert intent(client, len(CSV)).status_code == 201
    response = intent(client, len(CSV) + 1)
    assert (response.status_code, response.json()["code"]) == (413, "QUOTA_EXCEEDED")


@pytest.mark.parametrize(("count", "allowed"), [(10, True), (11, False)])
def test_at_most_10_files_go_into_one_run(count, allowed):
    from app.api.problem import ProblemError
    from app.files.service import check_files_per_run

    if allowed:
        check_files_per_run(count)
    else:
        with pytest.raises(ProblemError) as caught:
            check_files_per_run(count)
        assert (caught.value.problem.status, caught.value.problem.code) == (413, "QUOTA_EXCEEDED")
