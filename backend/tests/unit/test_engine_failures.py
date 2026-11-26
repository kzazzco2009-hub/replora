"""P3.4 failure semantics (T3.3): required branch → FAILED, optional → PARTIAL, low confidence →
NEEDS_REVIEW."""

from uuid import uuid4

from engine_samples import Spy, diamond, queued
from validator_samples import REGISTRY, definition, edge, file_input, node, output

from app.core.artifact_type import ArtifactType as T
from app.core.artifacts import ArtifactLineage
from app.core.engine.executor import OperationError, Result, execute
from app.core.engine.store import ArtifactStore, Data
from app.core.run_issue_codes import RunIssueCode as R
from app.core.run_state import RunState
from app.core.workflow import ReviewPolicy


def run_it(defn, spy, inputs=None, handlers=None):
    store = ArtifactStore(workspace_id=uuid4())
    refs = {name: store.put(Data(b"id,amount\n", "csv"), T.RAW_FILE, ArtifactLineage())
            for name in inputs or ()}  # fmt: skip
    return execute(queued(defn), REGISTRY, handlers or {("pass", 1): spy}, store, refs)


def summary(result):
    return [(i.code, i.node_id, i.path) for i in result.issues]


def test_a_failed_optional_branch_gives_partial_with_a_warning():
    spy = Spy(fail={"b"})
    result = run_it(diamond(), spy)
    assert result.run.state is RunState.PARTIAL
    assert summary(result) == [(R.NODE_FAILED, "b", "nodes/2")]
    assert result.issues[0].params == {"error": "CSV_UNREADABLE", "row": 3}
    assert spy.calls == ["a", "c", "b", "d"]
    assert "result" in result.outputs


def reconcile():
    """Two parsed files feed the required ports of `reconcile`; its report is the output."""
    return definition(
        [node("orders", "parse_csv"), node("payments", "parse_csv"),
         node("compare", "reconcile", key="id")],
        [edge("orders", "compare", "table", "left"), edge("payments", "compare", "table", "right")],
        [file_input("orders_file", "orders"), file_input("payments_file", "payments")],
        [output("report", "compare", "report")],
    )  # fmt: skip


def test_a_failed_required_branch_gives_failed_and_skips_what_needs_it():
    calls = []

    def parse(inputs, params):
        calls.append("parse")
        if len(calls) == 2:
            raise OperationError("CSV_UNREADABLE")
        return Result(outputs={"table": inputs["file"]})

    def compare(inputs, params):
        calls.append("compare")
        raise AssertionError("must not run without its required input")

    handlers = {("parse_csv", 1): parse, ("reconcile", 1): compare}
    result = run_it(reconcile(), None, ["orders_file", "payments_file"], handlers)
    assert result.run.state is RunState.FAILED
    assert summary(result) == [
        (R.NODE_FAILED, "payments", "nodes/1"),
        (R.NODE_SKIPPED, "compare", "nodes/2"),
        (R.OUTPUT_MISSING, None, "outputs/0"),
    ]
    assert result.issues[1].params == {"port": "right", "source": "payments"}
    assert calls == ["parse", "parse"]
    assert result.outputs == {}


def test_a_failed_node_feeding_a_workflow_output_gives_failed():
    result = run_it(diamond(), Spy(fail={"d"}))
    assert result.run.state is RunState.FAILED
    assert [i.code for i in result.issues] == [R.NODE_FAILED, R.OUTPUT_MISSING]


def test_low_confidence_stops_the_run_for_review():
    spy = Spy(warn={"b"})
    result = run_it(diamond(), spy)
    assert result.run.state is RunState.NEEDS_REVIEW
    assert [(i.code, i.node_id) for i in result.issues] == [("LOW_CONFIDENCE", "b")]
    assert spy.calls == ["a", "c", "b"]


def test_a_continue_policy_keeps_the_warning_and_finishes():
    spy = Spy(warn={"b"})
    result = run_it(diamond(review_policy=ReviewPolicy(on_warning="continue")), spy)
    assert result.run.state is RunState.SUCCEEDED
    assert [(i.code, i.node_id) for i in result.issues] == [("LOW_CONFIDENCE", "b")]
    assert spy.calls == ["a", "c", "b", "d"]
