"""Outputs (P7.2, P7.3): the comparison report as CSV, its summary as JSON, and both as a ZIP.

Every CSV cell goes through `escape_cell` (S-37): a cell starting with `= + - @`, tab or CR gets
a leading `'`, so a spreadsheet shows it as text instead of running it. A plain number (`-10`)
can't be a formula and is left alone, so the numbers stay numbers. CSVs are UTF-8 **with** a BOM
by default, so Arabic opens correctly in Excel; plain UTF-8 is an option. The summary and the ZIP
carry no timestamps, so the same inputs always give the same bytes.
"""

import csv
import io
import json
import re
import zipfile
from typing import Any

from app.core.engine.executor import OperationError
from app.ops.table import Table

FORMULA_START = ("=", "+", "-", "@", "\t", "\r")
PLAIN_NUMBER = re.compile(r"-?\d+(\.\d+)?")
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def escape_cell(cell: str) -> str:
    if cell.startswith(FORMULA_START) and not PLAIN_NUMBER.fullmatch(cell):
        return f"'{cell}"
    return cell


def _source(source: dict | None, field: str) -> str:
    return "" if source is None else str(source.get(field, ""))


def report_csv(report: dict[str, Any], params: dict[str, Any]) -> bytes:
    key, value = report["key"], report["value"]
    header = [key, "status", f"left_{value}", f"right_{value}", "difference",
              "left_file", "left_member", "left_row", "right_file", "right_member", "right_row",
              "operations"]  # fmt: skip
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\r\n")
    writer.writerow(map(escape_cell, header))
    for row in report["rows"]:
        left, right = row["left_source"], row["right_source"]
        ops = " | ".join(" ".join(side.get("ops", [])) for side in (left, right) if side)
        cells = [row["key"], row["status"], row["left"], row["right"], row["difference"],
                 *(_source(left, f) for f in ("file", "member", "row")),
                 *(_source(right, f) for f in ("file", "member", "row")), ops]  # fmt: skip
        writer.writerow(map(escape_cell, cells))
    return out.getvalue().encode(params.get("encoding", "utf-8-sig"))


def summary_json(report: dict[str, Any], params: dict[str, Any]) -> bytes:
    body = {"key": report["key"], "value": report["value"], "rows": len(report["rows"]),
            "summary": report["summary"]}  # fmt: skip
    return json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n"


def bundle_zip(files: dict[str, bytes]) -> bytes:
    """The same bytes on every machine: a fixed time and OS byte, and members stored as they are.

    Deflate output depends on the zlib build (Python on Windows ships zlib-ng), so compressing
    would make the bundle differ between a developer's machine and the server.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=FIXED_TIME)
            info.create_system = 3
            archive.writestr(info, data)
    return buffer.getvalue()


def map_columns(table: Table, params: dict[str, Any]) -> Table:
    """Rename columns, e.g. to line two files up. A missing or clashing name fails."""
    mapping: dict[str, str] = params["mapping"]
    for old in mapping:
        if old not in table.columns:
            raise OperationError("COLUMN_MISSING", column=old)
    columns = [mapping.get(name, name) for name in table.columns]
    if len(set(columns)) != len(columns):
        raise OperationError("COLUMN_CLASH", columns=columns)
    return Table(columns, table.rows, table.lineage)
