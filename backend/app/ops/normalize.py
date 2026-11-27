"""`normalize` (P7.2): trim and case the key, read number and date columns, report what fails.

Params: `key` and `key_case` (`upper`, `lower` or `as_is`), `numbers` and `dates` (column lists),
and `date_orders` (`{column: "DMY" | "MDY"}`, the answer to a `DATE_AMBIGUOUS` review).
"""

from typing import Any

from app.core.engine.executor import OperationError
from app.core.validation import Issue
from app.ops.dates import read_dates
from app.ops.numbers import read_decimal
from app.ops.table import Table

CASES = {"upper": str.upper, "lower": str.lower, "as_is": str}


def _index(table: Table, column: str) -> int:
    if column not in table.columns:
        raise OperationError("COLUMN_MISSING", column=column)
    return table.column(column)


def normalize(table: Table, params: dict[str, Any]) -> tuple[Table, list[Issue]]:
    rows = [list(row) for row in table.rows]
    warnings: list[Issue] = []
    if key := params.get("key"):
        at, case = _index(table, key), CASES[params.get("key_case", "as_is")]
        for row in rows:
            row[at] = case(row[at].strip())
    for column in params.get("numbers", []):
        at, bad = _index(table, column), []
        for row, source in zip(rows, table.lineage, strict=True):
            try:
                value = read_decimal(row[at])
            except ValueError:
                bad.append(source["row"])
                value = None
            row[at] = "" if value is None else str(value)
        if bad:
            warnings.append(Issue(code="NUMBER_INVALID", path="rows",
                                  params={"column": column, "rows": bad}))  # fmt: skip
    for column in params.get("dates", []):
        at = _index(table, column)
        order = params.get("date_orders", {}).get(column)
        try:
            values, options = read_dates([row[at] for row in rows], order)
        except ValueError:
            warnings.append(Issue(code="DATE_INVALID", path="rows", params={"column": column}))
            continue
        if options:
            warnings.append(Issue(code="DATE_AMBIGUOUS", path="rows",
                                  params={"column": column, "options": options}))  # fmt: skip
            continue
        for row, value in zip(rows, values, strict=True):
            row[at] = value
    return Table(table.columns, rows, table.lineage), warnings
