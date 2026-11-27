"""File facts for the TemplatePlanner (P8.1): column names, kinds and uniqueness, never rows."""

from typing import Literal

from app.core.planner.template import Column, FileFacts
from app.ops.csv_adapter import parse_csv
from app.ops.dates import read_dates
from app.ops.json_adapter import parse_json
from app.ops.numbers import read_decimal

PARSERS = {"csv": parse_csv, "json": parse_json}


def file_facts(label: str, format_: Literal["csv", "json"], content: bytes) -> FileFacts:
    """Parse the file with its P7 adapter. An unreadable file raises its `OperationError`."""
    table, _ = PARSERS[format_](content, {})
    columns = []
    for index, name in enumerate(table.columns):
        values = [row[index] for row in table.rows if row[index].strip()]
        columns.append(Column(name=name, kind=_kind(values),
                              unique=bool(values) and len(set(values)) == len(values)))  # fmt: skip
    return FileFacts(label=label, format=format_, columns=columns)


def _kind(values: list[str]) -> Literal["text", "number", "date"]:
    if not values:
        return "text"
    for kind, read in (("number", lambda: [read_decimal(v) for v in values]),
                       ("date", lambda: read_dates(values))):  # fmt: skip
        try:
            read()
        except ValueError:
            continue
        return kind
    return "text"
