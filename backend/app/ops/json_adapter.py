"""The JSON adapter (P7.1): an array of objects to a `Table`.

Nested objects flatten to dotted columns (`customer.city`); lists stay as JSON text. Number text
is kept exactly as written, for `normalize` to read as a Decimal. Mixed key sets become one set of
columns and are reported. Duplicate keys and nesting deeper than `MAX_DEPTH` fail.
"""

import json
from typing import Any

from app.core.engine.executor import OperationError
from app.core.validation import Issue
from app.ops.csv_adapter import decode
from app.ops.table import Table

MAX_DEPTH = 10


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise OperationError("JSON_DUPLICATE_KEY", key=next(k for k in keys if keys.count(k) > 1))
    return dict(pairs)


def _depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max(map(_depth, value.values()), default=0)
    if isinstance(value, list):
        return 1 + max(map(_depth, value), default=0)
    return 0


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _flat(record: dict[str, Any], prefix: str = "") -> dict[str, str]:
    cells: dict[str, str] = {}
    for key, value in record.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            cells |= _flat(value, f"{name}.")
        else:
            cells[name] = _text(value)
    return cells


def parse_json(data: bytes, source: dict[str, Any]) -> tuple[Table, list[Issue]]:
    try:
        records = json.loads(decode(data), object_pairs_hook=_no_duplicates,
                             parse_float=str, parse_int=str)  # fmt: skip
    except ValueError as error:
        raise OperationError("JSON_INVALID") from error
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise OperationError("JSON_NOT_ARRAY")
    if not records:
        raise OperationError("JSON_EMPTY")
    if _depth(records) > MAX_DEPTH + 1:
        raise OperationError("JSON_TOO_DEEP", limit=MAX_DEPTH)
    flat = [_flat(record) for record in records]
    columns = list(dict.fromkeys(name for cells in flat for name in cells))
    first = set(flat[0])
    mixed = [index for index, cells in enumerate(flat, start=1) if set(cells) != first]
    rows = [[cells.get(name, "") for name in columns] for cells in flat]
    lineage = [{**source, "row": index} for index in range(1, len(rows) + 1)]
    warnings = [Issue(code="JSON_KEYS_MIXED", path="rows", params={"rows": mixed})] if mixed else []
    return Table(columns, rows, lineage), warnings
