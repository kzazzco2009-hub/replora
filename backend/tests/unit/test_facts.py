"""P8.1: what the TemplatePlanner learns about a stored file: its columns, never its rows."""

import json

from app.core.planner.template import Column
from app.ops.facts import file_facts

CSV = "order_id,amount,paid_on,note\nO-1,100,25/04/2026,a\nO-2,(20),2026-04-26,a\nO-3,,,b\n"


def test_csv_columns_get_their_kind_and_uniqueness():
    facts = file_facts("orders.csv", "csv", CSV.encode())

    assert (facts.label, facts.format) == ("orders.csv", "csv")
    assert facts.columns == [
        Column(name="order_id", kind="text", unique=True),
        Column(name="amount", kind="number", unique=True),
        Column(name="paid_on", kind="date", unique=True),
        Column(name="note", kind="text", unique=False),
    ]


def test_json_records_give_the_same_facts():
    rows = [{"order_id": "O-1", "amount": 10}, {"order_id": "O-1", "amount": 10}]

    facts = file_facts("payments.json", "json", json.dumps(rows).encode())

    assert facts.columns == [
        Column(name="order_id", kind="text", unique=False),
        Column(name="amount", kind="number", unique=False),
    ]


def test_an_empty_column_is_text():
    facts = file_facts("a.csv", "csv", b"id,blank\n1,\n2,\n")

    assert facts.columns[1] == Column(name="blank", kind="text", unique=False)
