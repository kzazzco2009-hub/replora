"""P0.5 / T0.4: `contracts/openapi.json` is generated from the app, and drift is detected."""

import json
from importlib.metadata import version

from app.export_openapi import check, render, write


def test_render_documents_health_with_package_version():
    document = json.loads(render())

    assert "/api/v1/health" in document["paths"]
    assert document["info"]["version"] == version("replora-backend")


def test_render_is_deterministic():
    assert render() == render()


def test_check_passes_after_write(tmp_path):
    target = tmp_path / "openapi.json"
    write(target)

    assert check(target) == 0


def test_check_fails_when_committed_file_drifted(tmp_path):
    target = tmp_path / "openapi.json"
    write(target)
    target.write_text(target.read_text(encoding="utf-8").replace("/api/v1/health", "/api/v1/old"))

    assert check(target) == 1


def test_check_fails_when_file_is_missing(tmp_path):
    assert check(tmp_path / "openapi.json") == 1
