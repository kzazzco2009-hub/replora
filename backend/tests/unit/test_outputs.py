"""P7.2 outputs and map_columns: report_csv (T7.2, T7.8, T7.12, S-37), summary_json, bundle_zip."""

import csv
import io
import json
import zipfile

import pytest

from app.core.engine.executor import OperationError
from app.ops.outputs import bundle_zip, escape_cell, map_columns, report_csv, summary_json
from app.ops.table import Table

ROW = {"key": "O-102", "status": "value_diff", "left": "200", "right": "190", "difference": "10",
       "left_source": {"file": "bundle.zip", "member": "orders.csv", "row": 3,
                       "ops": ["extract_member@1", "parse_csv@1"]},
       "right_source": {"file": "bundle.zip", "member": "payments.json", "row": 2,
                        "ops": ["extract_member@1", "parse_json@1"]}}  # fmt: skip
REPORT = {
    "key": "order_id",
    "value": "amount",
    "rows": [ROW],
    "summary": {"matched": 0, "value_diff": 1, "missing_left": 0, "missing_right": 0},
}


@pytest.mark.parametrize(("cell", "shown"), [
    ("=HYPERLINK(\"x\")", "'=HYPERLINK(\"x\")"), ("+1+1", "'+1+1"), ("-2+3", "'-2+3"),
    ("@SUM(A1)", "'@SUM(A1)"), ("\tx", "'\tx"), ("\rx", "'\rx"),
    ("-10", "-10"), ("-0.5", "-0.5"), ("safe", "safe"), ("", ""),
])  # fmt: skip
def test_formula_cells_are_escaped_but_plain_numbers_are_not(cell, shown):
    assert escape_cell(cell) == shown


def read(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))


def test_the_report_has_a_bom_by_default_and_each_row_names_its_sources():
    data = report_csv(REPORT, {})
    assert data.startswith(b"\xef\xbb\xbf")
    header, row = read(data)
    assert header[:5] == ["order_id", "status", "left_amount", "right_amount", "difference"]
    assert dict(zip(header, row, strict=True)) | {} == {
        "order_id": "O-102", "status": "value_diff", "left_amount": "200",
        "right_amount": "190", "difference": "10", "left_file": "bundle.zip",
        "left_member": "orders.csv", "left_row": "3", "right_file": "bundle.zip",
        "right_member": "payments.json", "right_row": "2",
        "operations": "extract_member@1 parse_csv@1 | extract_member@1 parse_json@1",
    }  # fmt: skip


def test_the_plain_utf8_option_has_no_bom_and_arabic_survives():
    arabic = {**REPORT, "rows": [{**ROW, "key": "طلب-١"}]}
    data = report_csv(arabic, {"encoding": "utf-8"})
    assert not data.startswith(b"\xef\xbb\xbf")
    assert read(data)[1][0] == "طلب-١"


def test_injected_cells_are_escaped_in_the_report():
    evil = {**REPORT, "rows": [{**ROW, "key": "=cmd|' /C calc'!A0"}]}
    assert read(report_csv(evil, {}))[1][0] == "'=cmd|' /C calc'!A0"


def test_the_summary_is_deterministic_json():
    first, second = summary_json(REPORT, {}), summary_json(REPORT, {})
    assert first == second
    assert json.loads(first) == {"key": "order_id", "value": "amount", "rows": 1,
                                 "summary": REPORT["summary"]}  # fmt: skip


def test_the_bundle_is_byte_identical_every_time():
    files = {
        "comparison_report.csv": report_csv(REPORT, {}),
        "summary.json": summary_json(REPORT, {}),
    }
    first, second = bundle_zip(files), bundle_zip(files)
    assert first == second
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        assert archive.namelist() == ["comparison_report.csv", "summary.json"]


def test_map_columns_renames_and_refuses_a_missing_or_clashing_column():
    table = Table(["Order No", "Total"], [["1", "5"]], [{"row": 2}])
    renamed = map_columns(table, {"mapping": {"Order No": "order_id", "Total": "amount"}})
    assert renamed.columns == ["order_id", "amount"] and renamed.rows == table.rows
    with pytest.raises(OperationError) as caught:
        map_columns(table, {"mapping": {"Missing": "x"}})
    assert caught.value.code == "COLUMN_MISSING"
    with pytest.raises(OperationError) as caught:
        map_columns(table, {"mapping": {"Order No": "Total"}})
    assert caught.value.code == "COLUMN_CLASH"
