"""P7.6 acceptance (T7.1–T7.4): ZIP + CSV + JSON reconciliation on the real engine and registry."""

import csv
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.artifact_type import ArtifactType as T
from app.core.artifacts import ArtifactLineage
from app.core.engine.executor import execute
from app.core.engine.run import approve, new_run, transition
from app.core.engine.store import ArtifactStore, Data
from app.core.run_state import RunAction, RunState
from app.core.validator import validate
from app.core.workflow import Edge, InputContract, Node, OutputContract, PortRef, WorkflowDefinition
from app.ops.registry import HANDLERS, REGISTRY

NOW = datetime(2026, 11, 27, 12, tzinfo=UTC)
EXPECTED = Path(__file__).parent / "fixtures" / "acceptance"
ORDERS = "order_id,amount\nO-101,100\nO-102,200\nO-103,300\n"
PAYMENTS = [{"order_id": "O-101", "amount": 100}, {"order_id": "O-102", "amount": 190},
            {"order_id": "O-104", "amount": 50}]  # fmt: skip


def node(node_id: str, op: str, **params) -> Node:
    return Node(id=node_id, operation={"id": op, "version": 1}, params=params)


def wire(source: str, out: str, target: str, port: str) -> Edge:
    return Edge(source=PortRef(node_id=source, port=out), target=PortRef(node_id=target, port=port))


PIPELINE = WorkflowDefinition(
    nodes=[
        node("orders_member", "extract_member", path="orders.csv"),
        node("payments_member", "extract_member", path="payments.json"),
        node("orders", "parse_csv"), node("payments", "parse_json"),
        node("orders_clean", "normalize", key="order_id", numbers=["amount"]),
        node("payments_clean", "normalize", key="order_id", numbers=["amount"]),
        node("compare", "compare", key="order_id", value="amount"),
        node("report", "report_csv"), node("summary", "summary_json"), node("bundle", "bundle_zip"),
    ],
    edges=[
        wire("orders_member", "file", "orders", "file"),
        wire("payments_member", "file", "payments", "file"),
        wire("orders", "table", "orders_clean", "table"),
        wire("payments", "table", "payments_clean", "table"),
        wire("orders_clean", "table", "compare", "left"),
        wire("payments_clean", "table", "compare", "right"),
        wire("compare", "report", "report", "report"),
        wire("compare", "report", "summary", "report"),
        wire("report", "file", "bundle", "report"), wire("summary", "file", "bundle", "summary"),
    ],
    inputs=[InputContract(name="bundle", artifact_type=T.RAW_FILE,
                          targets=[PortRef(node_id="orders_member", port="archive"),
                                   PortRef(node_id="payments_member", port="archive")])],
    outputs=[OutputContract(name=name, artifact_type=T.OUTPUT_FILE,
                            source=PortRef(node_id=node_id, port="file"))
             for name, node_id in (("comparison_report", "report"), ("summary", "summary"),
                                   ("results", "bundle"))],
)  # fmt: skip


def archive(members: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as handle:
        for name, text in members.items():
            handle.writestr(name, text)
    return buffer.getvalue()


def run(members: dict[str, str]):
    store = ArtifactStore(uuid4())
    upload = store.put(Data(archive(members), "zip", {"file": "bundle.zip"}), T.RAW_FILE,
                       ArtifactLineage())  # fmt: skip
    queued = transition(transition(new_run(PIPELINE, NOW), RunAction.VALIDATE, NOW),
                        RunAction.REQUEST_APPROVAL, NOW)  # fmt: skip
    queued = approve(queued, queued.plan_hash, uuid4(), NOW)
    result = execute(queued, REGISTRY, HANDLERS, store, {"bundle": upload}, clock=lambda: NOW)
    return result, {name: store.read(ref).content for name, ref in result.outputs.items()}


GOOD = {"orders.csv": ORDERS, "payments.json": json.dumps(PAYMENTS)}


def test_the_pipeline_is_valid_against_the_real_registry():
    assert validate(PIPELINE, REGISTRY).valid


def test_the_acceptance_files_give_the_four_outcomes_and_the_expected_bytes():
    result, files = run(GOOD)
    assert result.run.state is RunState.SUCCEEDED
    rows = list(csv.DictReader(io.StringIO(files["comparison_report"].decode("utf-8-sig"))))
    assert {row["order_id"]: row["status"] for row in rows} == {
        "O-101": "matched", "O-102": "value_diff", "O-103": "missing_right",
        "O-104": "missing_left"}  # fmt: skip
    assert files["comparison_report"] == (EXPECTED / "comparison_report.csv").read_bytes()
    assert files["summary"] == (EXPECTED / "summary.json").read_bytes()
    assert files["results"] == (EXPECTED / "results.zip").read_bytes()


def test_every_report_row_names_its_file_member_row_and_operations():
    _, files = run(GOOD)
    rows = list(csv.DictReader(io.StringIO(files["comparison_report"].decode("utf-8-sig"))))
    o102 = next(row for row in rows if row["order_id"] == "O-102")
    left = (o102["left_file"], o102["left_member"], o102["left_row"])
    assert left == ("bundle.zip", "orders.csv", "3")
    assert (o102["right_member"], o102["right_row"]) == ("payments.json", "2")
    assert o102["operations"] == ("extract_member@1 parse_csv@1 normalize@1 | "
                                  "extract_member@1 parse_json@1 normalize@1")  # fmt: skip
    assert all(row["operations"] for row in rows)


def test_a_missing_required_branch_fails_and_never_reports_success():
    result, files = run({"orders.csv": ORDERS})
    assert result.run.state is RunState.FAILED
    assert files == {}
    assert [i.code for i in result.issues][0] == "NODE_FAILED"
    assert result.issues[0].params["error"] == "ZIP_MEMBER_MISSING"


@pytest.mark.parametrize("renamed", ["total"])
def test_schema_drift_stops_the_run_for_review(renamed):
    drifted = [{"order_id": p["order_id"], renamed: p["amount"]} for p in PAYMENTS]
    result, _ = run({"orders.csv": ORDERS, "payments.json": json.dumps(drifted)})
    assert result.run.state is RunState.NEEDS_REVIEW
    drift = next(i for i in result.issues if i.code == "SCHEMA_DRIFT")
    assert (drift.node_id, drift.params["column"]) == ("payments_clean", "amount")
    assert renamed in drift.params["available"]
