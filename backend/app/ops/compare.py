"""`compare` (P7.2): two tables on a key, value by value, with a Decimal tolerance (default exact).

Each key is `matched`, `value_diff`, `missing_right` (only on the left) or `missing_left`. A key
that appears twice on either side can't be paired safely: every one of its rows is listed as
`duplicate_key` and the duplication is reported (T7.9). Each report row keeps both rows' lineage.
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any

from app.core.engine.executor import OperationError
from app.core.validation import Issue
from app.ops.numbers import read_decimal
from app.ops.table import Table

OUTCOMES = ("matched", "value_diff", "missing_left", "missing_right")


def _positions(table: Table, key: int) -> dict[str, list[int]]:
    found = defaultdict(list)
    for index, row in enumerate(table.rows):
        found[row[key]].append(index)
    return found


def _columns(table: Table, side: str, *names: str) -> list[int]:
    for name in names:
        if name not in table.columns:
            raise OperationError("COLUMN_MISSING", column=name, side=side)
    return [table.column(name) for name in names]


def _difference(left: str, right: str, tolerance: Decimal) -> tuple[str, str]:
    a, b = read_decimal(left), read_decimal(right)
    if a is None or b is None:
        return ("matched" if a == b else "value_diff"), ""
    gap = a - b
    return ("matched" if abs(gap) <= tolerance else "value_diff"), str(gap)


def compare(left: Table, right: Table, params: dict[str, Any]) -> tuple[dict, list[Issue]]:
    key, value = params["key"], params["value"]
    tolerance = Decimal(params.get("tolerance", "0"))
    (lk, lv), (rk, rv) = _columns(left, "left", key, value), _columns(right, "right", key, value)
    lpos, rpos = _positions(left, lk), _positions(right, rk)
    warnings = [Issue(code="KEY_DUPLICATED", path="rows", params={"side": side, "keys": keys})
                for side, pos in (("left", lpos), ("right", rpos))
                if (keys := sorted(k for k, rows in pos.items() if len(rows) > 1))]  # fmt: skip
    rows = []
    for k in dict.fromkeys([*lpos, *rpos]):
        here, there = lpos.get(k, []), rpos.get(k, [])
        if len(here) > 1 or len(there) > 1:
            rows += [_row(k, "duplicate_key", left, i, None, None, lv, rv) for i in here]
            rows += [_row(k, "duplicate_key", None, None, right, j, lv, rv) for j in there]
        elif here and there:
            status, gap = _difference(left.rows[here[0]][lv], right.rows[there[0]][rv], tolerance)
            rows.append(
                _row(k, status, left, here[0], right, there[0], lv, rv) | {"difference": gap}
            )
        elif here:
            rows.append(_row(k, "missing_right", left, here[0], None, None, lv, rv))
        else:
            rows.append(_row(k, "missing_left", None, None, right, there[0], lv, rv))
    summary = {outcome: sum(row["status"] == outcome for row in rows) for outcome in OUTCOMES}
    return {"key": key, "value": value, "rows": rows, "summary": summary}, warnings


def _row(key, status, left, i, right, j, lv, rv) -> dict[str, Any]:
    return {
        "key": key, "status": status, "difference": "",
        "left": left.rows[i][lv] if left else "", "right": right.rows[j][rv] if right else "",
        "left_source": left.lineage[i] if left else None,
        "right_source": right.lineage[j] if right else None,
    }  # fmt: skip
