"""P7.1 the JSON adapter (T7.7) and taking one member out of a ZIP."""

import io
import json
import zipfile

import pytest

from app.core.engine.executor import OperationError
from app.ops.json_adapter import MAX_DEPTH, parse_json
from app.ops.zip_adapter import extract_member

SOURCE = {"file": "payments.json"}


def test_an_array_of_objects_becomes_a_table_with_exact_number_text():
    table, warnings = parse_json(b'[{"order_id": "O-101", "amount": 100.10}, '
                                 b'{"order_id": "O-102", "amount": 190}]', SOURCE)  # fmt: skip
    assert table.columns == ["order_id", "amount"]
    assert table.rows == [["O-101", "100.10"], ["O-102", "190"]]
    assert table.lineage == [
        {"file": "payments.json", "row": 1},
        {"file": "payments.json", "row": 2},
    ]
    assert warnings == []


def test_nested_objects_flatten_to_dotted_columns_and_lists_stay_json():
    table, _ = parse_json(b'[{"id": 1, "customer": {"name": "Salma", "city": {"en": "Cairo"}},'
                          b' "tags": ["a", "b"], "paid": true, "note": null}]', SOURCE)  # fmt: skip
    assert table.columns == ["id", "customer.name", "customer.city.en", "tags", "paid", "note"]
    assert table.rows == [["1", "Salma", "Cairo", '["a", "b"]', "true", ""]]


def test_mixed_key_sets_become_one_set_of_columns_and_are_reported():
    table, warnings = parse_json(b'[{"a": 1, "b": 2}, {"a": 3, "c": 4}]', SOURCE)
    assert (table.columns, table.rows) == (["a", "b", "c"], [["1", "2", ""], ["3", "", "4"]])
    assert [(w.code, w.params) for w in warnings] == [("JSON_KEYS_MIXED", {"rows": [2]})]


@pytest.mark.parametrize(("data", "code"), [
    (b'{"a": 1}', "JSON_NOT_ARRAY"),
    (b"[1, 2]", "JSON_NOT_ARRAY"),
    (b'[{"a": 1, "a": 2}]', "JSON_DUPLICATE_KEY"),
    (b"[" + b'{"a": ' * (MAX_DEPTH + 1) + b"1" + b"}" * (MAX_DEPTH + 1) + b"]", "JSON_TOO_DEEP"),
    (b"[]", "JSON_EMPTY"),
])  # fmt: skip
def test_unusable_json_fails_with_a_code(data, code):
    with pytest.raises(OperationError) as caught:
        parse_json(data, SOURCE)
    assert caught.value.code == code


def bundle() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("data/orders.csv", "id\n1\n")
        archive.writestr("payments.json", json.dumps([{"id": 1}]))
    return buffer.getvalue()


def test_a_member_is_taken_out_with_its_path_as_lineage():
    data, source = extract_member(bundle(), "data/orders.csv", {"file": "bundle.zip"})
    assert (data, source) == (b"id\n1\n", {"file": "bundle.zip", "member": "data/orders.csv"})


def test_a_missing_member_fails_and_names_what_is_there():
    with pytest.raises(OperationError) as caught:
        extract_member(bundle(), "orders.csv", {"file": "bundle.zip"})
    found = ["data/orders.csv", "payments.json"]
    assert caught.value.code == "ZIP_MEMBER_MISSING"
    assert caught.value.params == {"path": "orders.csv", "found": found}
