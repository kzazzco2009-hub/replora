"""P7.1 the CSV adapter (T7.5): encodings, delimiters, quoting, ragged rows, empties, duplicates."""

import pytest

from app.core.engine.executor import OperationError
from app.ops.csv_adapter import parse_csv
from app.ops.table import Table

SOURCE = {"file": "orders.csv"}


def parse(data: bytes) -> Table:
    table, _ = parse_csv(data, SOURCE)
    return table


@pytest.mark.parametrize("data", [
    "id,name\n1,سلمى\n".encode(),
    "﻿id,name\n1,سلمى\n".encode(),
    "id,name\n1,سلمى\n".encode("utf-16"),
    "id,name\n1,سلمى\n".encode("cp1256"),
])  # fmt: skip
def test_the_encodings_all_read_the_same(data):
    assert (parse(data).columns, parse(data).rows) == (["id", "name"], [["1", "سلمى"]])


@pytest.mark.parametrize("delimiter", [",", ";", "\t"])
def test_the_delimiter_is_sniffed(delimiter):
    data = delimiter.join(["id", "amount"]).encode() + b"\n" + delimiter.join(["1", "10"]).encode()
    assert parse(data).rows == [["1", "10"]]


def test_quoted_fields_keep_their_newlines_and_delimiters():
    table = parse(b'id,note\n1,"two\nlines, and a comma"\n')
    assert table.rows == [["1", "two\nlines, and a comma"]]


def test_header_names_are_trimmed():
    assert parse(b" id , amount \n1,2\n").columns == ["id", "amount"]


def test_ragged_rows_are_reported_never_silently_fixed():
    table, warnings = parse_csv(b"id,amount\n1\n2,20\n3,30,extra\n", SOURCE)
    assert table.rows == [["1", ""], ["2", "20"], ["3", "30"]]
    assert [(w.code, w.params) for w in warnings] == [
        ("CSV_ROW_RAGGED", {"rows": [2, 4], "expected": 2})]  # fmt: skip


def test_each_row_knows_where_it_came_from():
    table = parse(b"id\na\nb\n")
    assert table.lineage == [{"file": "orders.csv", "row": 2}, {"file": "orders.csv", "row": 3}]


def test_a_header_only_file_is_an_empty_table():
    assert (parse(b"id,amount\n").columns, parse(b"id,amount\n").rows) == (["id", "amount"], [])


BROKEN = [
    (b"", "CSV_EMPTY"),
    (b"\n\n", "CSV_EMPTY"),
    (b"id,ID,id\n1,2,3\n", "CSV_DUPLICATE_HEADER"),
]


@pytest.mark.parametrize(("data", "code"), BROKEN)
def test_empty_files_and_duplicate_headers_fail(data, code):
    with pytest.raises(OperationError) as caught:
        parse(data)
    assert caught.value.code == code


def test_a_table_round_trips_through_its_artifact_form():
    table = parse(b"id,amount\n1,10\n")
    assert Table.from_data(table.to_data()) == table
