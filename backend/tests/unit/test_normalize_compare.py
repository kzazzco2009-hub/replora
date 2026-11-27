"""P7.2 normalize (numbers T7.6, dates T7.11) and compare (T7.9, T7.10, P7.5)."""

from decimal import Decimal

import pytest

from app.core.engine.executor import OperationError
from app.ops.compare import compare
from app.ops.dates import read_dates
from app.ops.normalize import normalize
from app.ops.numbers import read_decimal
from app.ops.table import Table


@pytest.mark.parametrize(("text", "value"), [
    ("1,234.50", Decimal("1234.50")), ("1.234,50", Decimal("1234.50")), ("12,5", Decimal("12.5")),
    ("١٢٣", Decimal("123")), ("١٬٢٣٤٫٥", Decimal("1234.5")), ("۴۵", Decimal("45")),
    ("(100)", Decimal("-100")), ("-7.25", Decimal("-7.25")), (" 42 ", Decimal("42")),
    ("", None), ("NaN", None), ("nan", None),
])  # fmt: skip
def test_numbers_are_read_as_decimals(text, value):
    assert read_decimal(text) == value


@pytest.mark.parametrize("text", ["12abc", "1,2,3.4.5", "--1", "١٢x"])
def test_text_that_is_not_a_number_is_refused(text):
    with pytest.raises(ValueError):
        read_decimal(text)


def test_decimals_have_no_float_error():
    assert read_decimal("0.1") + read_decimal("0.2") == read_decimal("0.3")


@pytest.mark.parametrize(("values", "result"), [
    (["2026-04-03", "2026-12-25"], (["2026-04-03", "2026-12-25"], None)),
    (["25/04/2026", "03/04/2026"], (["2026-04-25", "2026-04-03"], None)),
    (["04/25/2026", "04/03/2026"], (["2026-04-25", "2026-04-03"], None)),
    (["03/04/2026", "05/06/2026"], (None, ["DMY", "MDY"])),
])  # fmt: skip
def test_dates_parse_unless_the_whole_column_is_ambiguous(values, result):
    assert read_dates(values) == result


def test_an_ambiguous_column_parses_once_the_format_is_chosen():
    assert read_dates(["03/04/2026"], "MDY") == (["2026-03-04"], None)


def table(columns, rows):
    return Table(columns, rows, [{"file": "f", "row": k + 2} for k in range(len(rows))])


def test_normalize_reads_numbers_dates_and_key_case():
    raw = table(["id", "amount", "paid"], [[" o-101 ", "1,234.50", "25/04/2026"]])
    out, warnings = normalize(raw, {"key": "id", "key_case": "upper", "numbers": ["amount"],
                                    "dates": ["paid"]})  # fmt: skip
    assert (out.rows, warnings) == ([["O-101", "1234.50", "2026-04-25"]], [])
    assert out.lineage == raw.lineage


def test_normalize_reports_bad_numbers_and_ambiguous_dates():
    raw = table(["amount", "paid"], [["x1", "03/04/2026"], ["5", "05/06/2026"]])
    _, warnings = normalize(raw, {"numbers": ["amount"], "dates": ["paid"]})
    assert [(w.code, w.params) for w in warnings] == [
        ("NUMBER_INVALID", {"column": "amount", "rows": [2]}),
        ("DATE_AMBIGUOUS", {"column": "paid", "options": ["DMY", "MDY"]}),
    ]  # fmt: skip


def test_normalize_needs_its_columns():
    with pytest.raises(OperationError) as caught:
        normalize(table(["id"], [["1"]]), {"numbers": ["amount"]})
    assert (caught.value.code, caught.value.params) == ("COLUMN_MISSING", {"column": "amount"})


ORDERS = table(["order_id", "amount"], [["O-101", "100"], ["O-102", "200"], ["O-103", "300"]])
PAYMENTS = table(["order_id", "amount"], [["O-101", "100"], ["O-102", "190"], ["O-104", "50"]])


def statuses(report) -> dict[str, str]:
    return {row["key"]: row["status"] for row in report["rows"]}


def test_compare_gives_the_four_outcomes():
    report, warnings = compare(ORDERS, PAYMENTS, {"key": "order_id", "value": "amount"})
    assert statuses(report) == {"O-101": "matched", "O-102": "value_diff",
                                "O-103": "missing_right", "O-104": "missing_left"}  # fmt: skip
    assert report["summary"] == {"matched": 1, "value_diff": 1, "missing_left": 1,
                                 "missing_right": 1}  # fmt: skip
    diff = next(row for row in report["rows"] if row["key"] == "O-102")
    assert (diff["left"], diff["right"], diff["difference"]) == ("200", "190", "10")
    assert diff["left_source"] == {"file": "f", "row": 3} and warnings == []


@pytest.mark.parametrize(("tolerance", "status"), [(None, "value_diff"), ("0.01", "matched")])
def test_the_tolerance_is_a_parameter_and_exact_by_default(tolerance, status):
    left, right = table(["k", "v"], [["a", "100.004"]]), table(["k", "v"], [["a", "100.00"]])
    params = {"key": "k", "value": "v"} | ({"tolerance": tolerance} if tolerance else {})
    assert statuses(compare(left, right, params)[0]) == {"a": status}


def test_point_one_plus_point_two_matches_point_three():
    left, right = table(["k", "v"], [["a", "0.3"]]), table(["k", "v"], [["a", "0.30"]])
    assert statuses(compare(left, right, {"key": "k", "value": "v"})[0]) == {"a": "matched"}


def test_duplicate_keys_are_reported_and_listed_never_dropped():
    left = table(["k", "v"], [["a", "1"], ["a", "2"], ["b", "3"]])
    right = table(["k", "v"], [["a", "1"], ["b", "3"]])
    report, warnings = compare(left, right, {"key": "k", "value": "v"})
    assert [(row["key"], row["status"]) for row in report["rows"]] == [
        ("a", "duplicate_key"), ("a", "duplicate_key"), ("a", "duplicate_key"),
        ("b", "matched")]  # fmt: skip
    assert [(w.code, w.params) for w in warnings] == [
        ("KEY_DUPLICATED", {"side": "left", "keys": ["a"]})]  # fmt: skip


def test_a_key_duplicated_on_the_right_is_reported_too():
    left = table(["k", "v"], [["a", "1"]])
    right = table(["k", "v"], [["a", "1"], ["a", "1"]])
    report, warnings = compare(left, right, {"key": "k", "value": "v"})
    assert [row["status"] for row in report["rows"]] == ["duplicate_key"] * 3
    assert [w.params["side"] for w in warnings] == ["right"]
