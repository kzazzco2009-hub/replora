"""The CSV adapter (P7.1): bytes to a `Table`, never guessing silently.

Encoding: a BOM decides (UTF-8 or UTF-16), else UTF-8, else Windows-1256 (Arabic Excel). The
delimiter is sniffed among `,` `;` and tab. Quoted fields keep their newlines. Rows with the wrong
number of cells are padded or cut **and reported** (`CSV_ROW_RAGGED`). An empty file and duplicate
headers fail, because the rest of the workflow couldn't tell the columns apart.
"""

import codecs
import csv
import io
from typing import Any

from app.core.engine.executor import OperationError
from app.core.validation import Issue
from app.ops.table import Table

DELIMITERS = ",;\t"


def decode(data: bytes) -> str:
    if data.startswith(codecs.BOM_UTF8):
        return data[len(codecs.BOM_UTF8) :].decode("utf-8")
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1256")


def _dialect(text: str) -> str:
    try:
        return csv.Sniffer().sniff(text[:4096], delimiters=DELIMITERS).delimiter
    except csv.Error:
        return ","


def parse_csv(data: bytes, source: dict[str, Any]) -> tuple[Table, list[Issue]]:
    text = decode(data)
    if not text.strip():
        raise OperationError("CSV_EMPTY")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=_dialect(text))
    header, *records = [row for row in reader if row]
    columns = [name.strip() for name in header]
    duplicates = sorted({name for name in columns if columns.count(name) > 1})
    if duplicates:
        raise OperationError("CSV_DUPLICATE_HEADER", columns=duplicates)
    rows, lineage, ragged = [], [], []
    line = 1
    for record in records:
        line += 1
        if len(record) != len(columns):
            ragged.append(line)
        rows.append((record + [""] * len(columns))[: len(columns)])
        lineage.append({**source, "row": line})
    params = {"rows": ragged, "expected": len(columns)}
    warnings = [Issue(code="CSV_ROW_RAGGED", path="rows", params=params)] if ragged else []
    return Table(columns, rows, lineage), warnings
