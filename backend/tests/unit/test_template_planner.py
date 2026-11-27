"""P3.9 TemplatePlanner, the "reconcile" template (T3.11)."""

import pytest
from validator_samples import op

from app.core.artifact_type import ArtifactType as T
from app.core.operations import Port
from app.core.plan_hash import plan_hash
from app.core.planner.template import TEMPLATES, Column, FileFacts, plan
from app.core.planner_codes import PlannerCode as P
from app.core.registry import OperationRegistry
from app.core.validator import validate

# The operations the templates use. Phase 7 registers the real ones under the same ids.
REGISTRY = OperationRegistry([
    op("parse_csv", [Port(name="file", artifact_type=T.RAW_FILE, required=True)],
       [Port(name="table", artifact_type=T.TABULAR, required=True)]),
    op("parse_json", [Port(name="file", artifact_type=T.RAW_FILE, required=True)],
       [Port(name="table", artifact_type=T.TABULAR, required=True)]),
    op("compare", [Port(name="left", artifact_type=T.TABULAR, required=True),
                   Port(name="right", artifact_type=T.TABULAR, required=True)],
       [Port(name="report", artifact_type=T.COMPARISON_REPORT, required=True)],
       required=["key", "value"],
       properties={"key": {"type": "string"}, "value": {"type": "string"}}),
    op("report_csv", [Port(name="report", artifact_type=T.COMPARISON_REPORT, required=True)],
       [Port(name="file", artifact_type=T.OUTPUT_FILE, required=True)]),
])  # fmt: skip


def text(name, unique=False):
    return Column(name=name, kind="text", unique=unique)


def number(name, unique=False):
    return Column(name=name, kind="number", unique=unique)


ORDERS = FileFacts(label="orders.csv", format="csv", columns=[
    text("order_id", unique=True), text("customer"), number("amount", unique=True), text("date"),
])  # fmt: skip
PAYMENTS = FileFacts(label="payments.json", format="json", columns=[
    text("order_id", unique=True), number("amount", unique=True), text("paid_at"),
])  # fmt: skip


def compare_params(draft):
    return next(n.params for n in draft.definition.nodes if n.id == "compare")


def test_the_reconcile_template_is_listed():
    assert TEMPLATES["reconcile"].required_inputs == (T.RAW_FILE, T.RAW_FILE)


def test_reconcile_picks_order_id_as_the_key_and_amount_as_the_value():
    draft = plan("reconcile", [ORDERS, PAYMENTS])
    assert compare_params(draft) == {"key": "order_id", "value": "amount"}
    assert draft.warnings == []
    assert validate(draft.definition, REGISTRY).valid
    assert draft.explanation.key == "plans.reconcile"
    assert draft.explanation.params == {"key": "order_id", "value": "amount",
                                        "left": "orders.csv", "right": "payments.json"}  # fmt: skip


def test_each_file_is_parsed_by_its_format_and_its_columns_are_the_input_contract():
    draft = plan("reconcile", [ORDERS, PAYMENTS])
    ops = {n.id: n.operation.id for n in draft.definition.nodes}
    assert ops == {"left": "parse_csv", "right": "parse_json", "compare": "compare",
                   "report": "report_csv"}  # fmt: skip
    left, right = draft.definition.inputs
    assert (left.label, left.columns) == ("orders.csv", ["order_id", "customer", "amount", "date"])
    assert (right.label, right.columns) == ("payments.json", ["order_id", "amount", "paid_at"])


def test_no_shared_unique_column_gives_a_warning_never_a_guess():
    other = FileFacts(label="b.csv", format="csv", columns=[text("ref", unique=True),
                                                           number("amount")])  # fmt: skip
    draft = plan("reconcile", [ORDERS, other])
    assert [(w.code, w.path) for w in draft.warnings] == [(P.KEY_NOT_FOUND, "nodes/2/params/key")]
    assert "key" not in compare_params(draft)
    assert [i.code for i in validate(draft.definition, REGISTRY).errors] == ["PARAM_INVALID"]


def test_two_id_like_candidates_are_ambiguous():
    both = [text("order_id", unique=True), text("invoice_id", unique=True), number("amount")]
    a = FileFacts(label="a.csv", format="csv", columns=both)
    draft = plan("reconcile", [a, a])
    assert [(w.code, w.params) for w in draft.warnings] == [
        (P.KEY_AMBIGUOUS, {"candidates": ["order_id", "invoice_id"]})
    ]
    assert "key" not in compare_params(draft)


def test_a_missing_value_column_is_a_warning():
    a = FileFacts(label="a.csv", format="csv", columns=[text("id", unique=True), text("x")])
    draft = plan("reconcile", [a, a])
    assert [w.code for w in draft.warnings] == [P.VALUE_NOT_FOUND]
    assert compare_params(draft) == {"key": "id"}


def test_a_numeric_key_is_not_also_the_value():
    a = FileFacts(label="a.csv", format="csv", columns=[number("id", unique=True), number("qty")])
    draft = plan("reconcile", [a, a])
    assert (compare_params(draft), draft.warnings) == ({"key": "id", "value": "qty"}, [])


def test_name_hints_ignore_case():
    a = FileFacts(label="a.csv", format="csv",
                  columns=[text("Customer", unique=True), text("Order_ID", unique=True),
                           number("Amount")])  # fmt: skip
    assert compare_params(plan("reconcile", [a, a])) == {"key": "Order_ID", "value": "Amount"}


def test_matching_is_exact_after_unicode_normalization_and_trimming():
    spaced = FileFacts(label="b.csv", format="csv",
                       columns=[text(" order_id ", unique=True), number("amount")])  # fmt: skip
    assert compare_params(plan("reconcile", [ORDERS, spaced])) == {"key": "order_id",
                                                                    "value": "amount"}  # fmt: skip
    upper = FileFacts(label="b.csv", format="csv",
                      columns=[text("ORDER_ID", unique=True), number("amount")])  # fmt: skip
    assert [w.code for w in plan("reconcile", [ORDERS, upper]).warnings] == [P.KEY_NOT_FOUND]


def test_the_plan_is_deterministic():
    hashes = {plan_hash(plan("reconcile", [ORDERS, PAYMENTS]).definition) for _ in range(5)}
    assert len(hashes) == 1


def test_arabic_column_names_work():
    left = FileFacts(label="الطلبات.csv", format="csv", columns=[
        text("رقم الطلب", unique=True), text("العميل"), number("المبلغ", unique=True),
    ])  # fmt: skip
    right = FileFacts(label="المدفوعات.json", format="json", columns=[
        text("رقم الطلب", unique=True), number("المبلغ", unique=True),
    ])  # fmt: skip
    draft = plan("reconcile", [left, right])
    assert compare_params(draft) == {"key": "رقم الطلب", "value": "المبلغ"}
    assert draft.warnings == []
    assert validate(draft.definition, REGISTRY).valid


def test_reconcile_needs_exactly_two_files():
    with pytest.raises(ValueError, match="2 files"):
        plan("reconcile", [ORDERS])
