"""P7.2 the real operation registry: contracts, handlers, lineage, and the operation_codes."""

import ast
import json
from pathlib import Path

from app.config import REPO_ROOT
from app.core.engine.executor import Result
from app.core.engine.store import Data
from app.ops.codes import OperationCode
from app.ops.registry import HANDLERS, REGISTRY
from app.ops.table import Table

OPS = Path(__file__).resolve().parents[2] / "app" / "ops"
TEMPLATE_OPS = {"parse_csv", "parse_json", "compare", "report_csv", "append_rows", "export_csv"}


def test_every_registered_operation_has_a_handler_and_the_templates_are_covered():
    registered = {(c.id, c.version) for c in REGISTRY.list()}
    assert registered == set(HANDLERS)
    assert {op for op, _ in registered} >= TEMPLATE_OPS


def raised_codes() -> set[str]:
    codes = set()
    for path in OPS.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "OperationError":
                codes.add(node.args[0].value)
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "Issue":
                codes |= {kw.value.value for kw in node.keywords
                          if kw.arg == "code" and isinstance(kw.value, ast.Constant)}  # fmt: skip
    return codes


def test_every_code_an_operation_can_give_is_in_the_catalogue():
    catalogue = json.loads((REPO_ROOT / "contracts" / "error-codes.json").read_text("utf-8"))
    assert raised_codes() <= set(OperationCode)
    assert set(catalogue["operation_codes"]) == set(OperationCode)


def run(op: str, inputs: dict[str, Data], **params) -> Result:
    return HANDLERS[op, 1](inputs, params)


def test_parse_csv_keeps_the_source_and_records_itself_in_the_lineage():
    result = run("parse_csv", {"file": Data(b"id\n1\n", "csv", {"file": "a.csv"})})
    table = Table.from_data(result.outputs["table"])
    assert table.lineage == [{"file": "a.csv", "row": 2, "ops": ["parse_csv@1"]}]


def test_extract_then_parse_names_the_member():
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("orders.csv", "id\n1\n")
    member = run("extract_member", {"archive": Data(buffer.getvalue(), "zip", {"file": "b.zip"})},
                 path="orders.csv").outputs["file"]  # fmt: skip
    table = Table.from_data(run("parse_csv", {"file": member}).outputs["table"])
    assert table.lineage[0] == {"file": "b.zip", "member": "orders.csv", "row": 2,
                                "ops": ["extract_member@1", "parse_csv@1"]}  # fmt: skip


def test_a_missing_column_in_normalize_is_schema_drift_for_review():
    table = Table(["order_id", "total"], [["O-1", "5"]], [{"row": 2}])
    result = run("normalize", {"table": table.to_data()}, key="order_id", numbers=["amount"])
    assert [(w.code, w.params) for w in result.warnings] == [
        ("SCHEMA_DRIFT", {"column": "amount", "available": ["order_id", "total"]})]  # fmt: skip
    assert Table.from_data(result.outputs["table"]).columns == ["order_id", "total"]


def test_append_rows_stacks_tables_with_the_same_columns():
    a = Table(["id"], [["1"]], [{"file": "a", "row": 2}]).to_data()
    b = Table(["id"], [["2"]], [{"file": "b", "row": 2}]).to_data()
    merged = Table.from_data(run("append_rows", {"in_0": a, "in_1": b}).outputs["table"])
    assert (merged.rows, [r["file"] for r in merged.lineage]) == ([["1"], ["2"]], ["a", "b"])
