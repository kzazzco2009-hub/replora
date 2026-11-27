"""P8.1 run outputs: list, preview, download, row lineage and the run's summary (T8.1)."""

import pytest
from web import reconciled, signed_in

from app.db import models as m


@pytest.fixture
def web(db_url, tmp_path):
    return signed_in(db_url, tmp_path)


def outputs(web, run, path=""):
    return f"/api/v1/workspaces/{web.ws}/runs/{run['id']}/outputs{path}"


def test_a_finished_run_counts_its_outcomes(web):
    run = reconciled(web)

    expected = {"matched": 1, "value_diff": 1, "missing_left": 1, "missing_right": 1}
    assert (run["state"], run["summary"]) == ("SUCCEEDED", expected)
    listed = web.get(f"/api/v1/workspaces/{web.ws}/runs").json()["items"][0]
    assert listed["summary"] == expected


def test_the_outputs_are_the_definitions_output_files(web):
    run = reconciled(web)

    response = web.get(outputs(web, run))

    assert response.status_code == 200
    [report] = response.json()
    assert (report["name"], report["type"], report["format"]) == (
        "report.csv", "OutputFile", "csv")  # fmt: skip
    assert report["size"] > 0


def test_a_download_is_a_signed_link_to_the_report_as_an_attachment(web):
    run = reconciled(web)
    [report] = web.get(outputs(web, run)).json()

    link = web.get(outputs(web, run, f"/{report['id']}/download")).json()
    body = web.get(link["url"])

    assert body.status_code == 200
    assert body.content.startswith(b"\xef\xbb\xbforder_id,status")
    assert body.headers["content-disposition"] == "attachment; filename*=UTF-8''report.csv"


def test_an_artifact_that_is_not_an_output_is_not_found(web):
    run = reconciled(web)
    with web.app.state.sessions() as session:
        internal = session.query(m.Artifact).filter(m.Artifact.node_id == "compare").one().id

    assert web.get(outputs(web, run, f"/{internal}/download")).status_code == 404


def test_another_workspace_sees_no_outputs(web, db_url, tmp_path):
    run = reconciled(web)
    other = signed_in(db_url, tmp_path / "other", email="o@example.com")

    assert other.get(f"/api/v1/workspaces/{other.ws}/runs/{run['id']}/outputs").status_code == 404


def report(web, run):
    return web.get(outputs(web, run)).json()[0]


def test_the_preview_pages_the_report_with_each_rows_status(web):
    run = reconciled(web)
    made = report(web, run)

    page = web.get(outputs(web, run, f"/{made['id']}/preview?limit=2")).json()

    assert [c["name"] for c in page["columns"]][:2] == ["order_id", "status"]
    assert (page["total"], page["offset"]) == (4, 0)
    assert [(r["row"], r["status"], r["cells"][0]) for r in page["rows"]] == [
        (0, "matched", "O-101"), (1, "value_diff", "O-102")]  # fmt: skip


def test_the_preview_filters_by_status_and_text(web):
    run = reconciled(web)
    made = report(web, run)
    preview = outputs(web, run, f"/{made['id']}/preview")

    missing = web.get(f"{preview}?status=missing_left").json()
    text = web.get(f"{preview}?q=o-103").json()

    assert [(r["row"], r["cells"][0]) for r in missing["rows"]] == [(3, "O-104")]
    assert [(r["row"], r["status"]) for r in text["rows"]] == [(2, "missing_right")]
    assert text["total"] == 1


def test_a_rows_lineage_names_its_source_files_rows_and_operations(web):
    run = reconciled(web)
    made = report(web, run)
    files = {f["display_name"]: f["id"]
             for f in web.get(f"/api/v1/workspaces/{web.ws}/files").json()["items"]}  # fmt: skip

    lineage = web.get(outputs(web, run, f"/{made['id']}/rows/1/lineage")).json()

    assert lineage["sources"] == [
        {"file_id": files["orders.csv"], "member_path": None, "row": 3, "page": None},
        {"file_id": files["payments.json"], "member_path": None, "row": 2, "page": None},
    ]
    assert lineage["operations"] == [{"id": "parse_csv", "version": 1},
                                     {"id": "parse_json", "version": 1}]  # fmt: skip


def test_a_row_past_the_end_has_no_lineage(web):
    run = reconciled(web)
    made = report(web, run)

    assert web.get(outputs(web, run, f"/{made['id']}/rows/4/lineage")).status_code == 404
