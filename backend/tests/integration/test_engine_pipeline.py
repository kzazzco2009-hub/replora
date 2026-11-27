"""T3.9 and T3.10: the fake ZIP → CSV and JSON branches → compare → report pipeline, end to end,
and its retry, idempotency, cancel, failure and replay scenarios (the original S1.4)."""

import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fakes import HANDLERS, PIPELINE, REGISTRY, MockPlanner

from app.core.artifact_type import ArtifactType as T
from app.core.artifacts import ArtifactLineage
from app.core.engine.executor import OperationError, TransientError, execute
from app.core.engine.replay import ReplayInput, start_replay
from app.core.engine.run import approve, new_run, transition
from app.core.engine.store import ArtifactStore, Data
from app.core.run_issue_codes import RunIssueCode as R
from app.core.run_state import RunAction, RunState
from app.core.validator import validate

NOW = datetime(2026, 11, 26, 12, tzinfo=UTC)
ORDERS = "order_id,amount\nA1,10\nA2,20\nA3,30\n"
PAYMENTS = [{"order_id": "A1", "amount": 10}, {"order_id": "A2", "amount": 25},
            {"order_id": "A4", "amount": 40}]  # fmt: skip
EXPECTED = (
    "key,status,left,right\nA1,match,10,10\nA2,mismatch,20,25\nA3,only_left,30,\n"
    "A4,only_right,,40\n"
)


def bundle() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("orders.csv", ORDERS)
        archive.writestr("payments.json", json.dumps(PAYMENTS))
    return buffer.getvalue()


def approved(definition):
    run = transition(new_run(definition, NOW), RunAction.VALIDATE, NOW)
    run = transition(run, RunAction.REQUEST_APPROVAL, NOW)
    return approve(run, run.plan_hash, uuid4(), NOW)


def pipeline(handlers=HANDLERS, run=None, **kwargs):
    store = kwargs.pop("store", None) or ArtifactStore(uuid4())
    upload = store.put(Data(bundle(), "zip"), T.RAW_FILE, ArtifactLineage())
    result = execute(run or approved(PIPELINE), REGISTRY, handlers, store, {"bundle": upload},
                     sleep=lambda _: None, **kwargs)  # fmt: skip
    return result, store


class Counting(dict):
    """The fake handlers, counting calls by operation; `fail` makes one operation raise."""

    def __init__(self, fail=None) -> None:
        super().__init__({key: self._wrap(key, fn) for key, fn in HANDLERS.items()})
        self.calls: list[str] = []
        self.fail = fail

    def _wrap(self, key, fn):
        def call(inputs, params):
            self.calls.append(key[0])
            if self.fail and self.fail[0] == key[0] and self.fail[1]:
                self.fail = (self.fail[0], self.fail[1] - 1, self.fail[2])
                raise self.fail[2]
            return fn(inputs, params)

        return call


def test_the_mock_planner_draft_is_valid():
    draft = MockPlanner().plan("reconcile the bundle", ["bundle.zip"])
    assert validate(draft.definition, REGISTRY).valid


def test_the_pipeline_runs_end_to_end_and_matches_the_expected_report():
    result, store = pipeline()
    assert (result.run.state, result.issues) == (RunState.SUCCEEDED, [])
    report = result.outputs["report"]
    assert store.read(report).content.decode() == EXPECTED
    assert (report.type, report.format, report.lineage.node_id) == (T.OUTPUT_FILE, "csv", "render")


def test_a_transient_failure_in_one_branch_is_retried():
    handlers = Counting(fail=("fake_parse_json", 2, TransientError("BUSY")))
    result, store = pipeline(handlers)
    assert result.run.state is RunState.SUCCEEDED
    assert handlers.calls.count("fake_parse_json") == 3
    assert store.read(result.outputs["report"]).content.decode() == EXPECTED


def test_a_second_attempt_with_the_same_ledger_executes_nothing_again():
    handlers, ledger, store, run = Counting(), {}, ArtifactStore(uuid4()), approved(PIPELINE)
    first, _ = pipeline(handlers, run, ledger=ledger, store=store)
    again, _ = pipeline(handlers, run, ledger=ledger, store=store)
    assert len(handlers.calls) == 5
    assert again.outputs["report"].sha256 == first.outputs["report"].sha256


def test_cancel_after_the_unzip_stops_both_branches():
    handlers = Counting()
    result, _ = pipeline(handlers, cancelled=lambda: handlers.calls == ["fake_unzip"])
    assert result.run.state is RunState.CANCELLED
    assert handlers.calls == ["fake_unzip"]


def test_a_failed_branch_fails_the_run_and_skips_compare_and_render():
    handlers = Counting(fail=("fake_parse_json", 1, OperationError("JSON_INVALID")))
    result, _ = pipeline(handlers)
    assert result.run.state is RunState.FAILED
    assert [(i.code, i.node_id) for i in result.issues] == [
        (R.NODE_FAILED, "payments"), (R.NODE_SKIPPED, "compare"), (R.NODE_SKIPPED, "render"),
        (R.OUTPUT_MISSING, None),
    ]  # fmt: skip
    assert "fake_compare" not in handlers.calls


def test_a_replay_of_the_saved_pipeline_gives_the_same_report_hash():
    saved = PIPELINE.model_copy(update={"workflow_id": uuid4(), "workflow_version": 1})
    first, store = pipeline(run=approved(saved))
    upload = store.put(Data(bundle(), "zip"), T.RAW_FILE, ArtifactLineage())
    run, issues = start_replay(saved, {"bundle": ReplayInput(upload, [])}, NOW)
    assert issues == []
    again, _ = pipeline(run=approve(run, run.plan_hash, uuid4(), NOW), store=store)
    assert again.outputs["report"].sha256 == first.outputs["report"].sha256


def test_the_mock_planner_and_fakes_are_test_only():
    app = Path(__file__).resolve().parents[2] / "app"
    offenders = [p for p in app.rglob("*.py") if "MockPlanner" in p.read_text(encoding="utf-8")]
    assert offenders == []
