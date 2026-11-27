"""P3.9 TemplatePlanner, the "merge files with the same columns" template."""

import pytest
from validator_samples import op

from app.core.artifact_type import ArtifactType as T
from app.core.operations import Port
from app.core.plan_hash import plan_hash
from app.core.planner.template import TEMPLATES, Column, FileFacts, plan
from app.core.planner_codes import PlannerCode as P
from app.core.registry import OperationRegistry
from app.core.validator import validate

REGISTRY = OperationRegistry([
    op("parse_csv", [Port(name="file", artifact_type=T.RAW_FILE, required=True)],
       [Port(name="table", artifact_type=T.TABULAR, required=True)]),
    op("parse_json", [Port(name="file", artifact_type=T.RAW_FILE, required=True)],
       [Port(name="table", artifact_type=T.TABULAR, required=True)]),
    op("append_rows", [Port(name=f"in_{k}", artifact_type=T.TABULAR, required=k < 2)
                       for k in range(10)],
       [Port(name="table", artifact_type=T.TABULAR, required=True)]),
    op("export_csv", [Port(name="table", artifact_type=T.TABULAR, required=True)],
       [Port(name="file", artifact_type=T.OUTPUT_FILE, required=True)]),
])  # fmt: skip


def facts(label, *names, fmt="csv"):
    return FileFacts(label=label, format=fmt,
                     columns=[Column(name=n, kind="text") for n in names])  # fmt: skip


JAN = facts("jan.csv", "order_id", "amount")
FEB = facts("feb.json", "amount", "order_id", fmt="json")
MAR = facts("mar.csv", "order_id", "amount")


def test_the_merge_template_takes_two_to_ten_files():
    spec = TEMPLATES["merge"]
    assert (spec.required_inputs, spec.max_inputs) == ((T.RAW_FILE, T.RAW_FILE), 10)


def test_files_with_the_same_columns_merge_in_the_given_order():
    draft = plan("merge", [JAN, FEB, MAR])
    assert draft.warnings == []
    assert validate(draft.definition, REGISTRY).valid
    ops = [(n.id, n.operation.id) for n in draft.definition.nodes]
    assert ops == [("file_0", "parse_csv"), ("file_1", "parse_json"), ("file_2", "parse_csv"),
                   ("merge", "append_rows"), ("export", "export_csv")]  # fmt: skip
    targets = [e.target.port for e in draft.definition.edges if e.target.node_id == "merge"]
    assert targets == ["in_0", "in_1", "in_2"]
    assert [i.label for i in draft.definition.inputs] == ["jan.csv", "feb.json", "mar.csv"]
    assert draft.explanation.key == "plans.merge"
    assert draft.explanation.params == {"files": 3}


def test_a_file_with_other_columns_is_a_warning_never_a_silent_merge():
    odd = facts("apr.csv", "order_id", "total", " amount ", "note")
    draft = plan("merge", [JAN, odd, facts("may.csv", "order_id")])
    assert [(w.code, w.path, w.params) for w in draft.warnings] == [
        (P.COLUMNS_DIFFER, "inputs/1", {"file": "apr.csv", "missing": [],
                                        "extra": ["total", "note"]}),
        (P.COLUMNS_DIFFER, "inputs/2", {"file": "may.csv", "missing": ["amount"], "extra": []}),
    ]  # fmt: skip


def test_arabic_columns_merge():
    a, b = facts("أ.csv", "رقم الطلب", "المبلغ"), facts("ب.csv", "المبلغ", "رقم الطلب")
    assert plan("merge", [a, b]).warnings == []


def test_the_merge_plan_is_deterministic():
    assert len({plan_hash(plan("merge", [JAN, FEB]).definition) for _ in range(5)}) == 1


@pytest.mark.parametrize("count", [1, 11])
def test_merge_needs_two_to_ten_files(count):
    with pytest.raises(ValueError, match="2 to 10 files"):
        plan("merge", [JAN] * count)
