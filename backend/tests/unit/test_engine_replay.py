"""P3.7 replay of a pinned workflow version on new inputs (T3.8)."""

from uuid import uuid4

import pytest
from engine_samples import NOW, Spy
from validator_samples import REGISTRY, definition, node, output

from app.core.artifact_type import ArtifactType as T
from app.core.artifacts import ArtifactLineage
from app.core.engine.executor import execute
from app.core.engine.replay import ReplayInput, start_replay
from app.core.engine.run import approve
from app.core.engine.store import ArtifactStore, Data
from app.core.run_issue_codes import RunIssueCode as R
from app.core.run_state import RunState
from app.core.workflow import InputContract, PortRef

USER = uuid4()


def saved(columns=("order_id", "amount")):
    feed = InputContract(name="orders", artifact_type=T.TABULAR, columns=list(columns),
                         targets=[PortRef(node_id="a", port="in_0")])  # fmt: skip
    defn = definition([node("a", tag="a")], [], [feed], [output("result", "a", "out", T.TABULAR)])
    return defn.model_copy(update={"workflow_id": uuid4(), "workflow_version": 3})


def upload(store, content=b"order_id,amount\n1,5\n", artifact_type=T.TABULAR):
    return store.put(Data(content, "csv"), artifact_type, ArtifactLineage())


def given(store, columns=("order_id", "amount", "note"), **kwargs):
    return {"orders": ReplayInput(ref=upload(store, **kwargs), columns=list(columns))}


def test_matching_inputs_give_a_run_awaiting_approval_of_the_same_plan():
    store, defn = ArtifactStore(uuid4()), saved()
    run, issues = start_replay(defn, given(store), NOW)
    assert (run.state, issues) == (RunState.AWAITING_APPROVAL, [])
    assert run.definition == defn
    assert run.approval is None


def test_missing_columns_stop_the_replay_for_review():
    store = ArtifactStore(uuid4())
    run, issues = start_replay(saved(), given(store, columns=["order_id"]), NOW)
    assert run.state is RunState.NEEDS_REVIEW
    assert [(i.code, i.path, i.params) for i in issues] == [
        (R.INPUT_COLUMNS_MISSING, "inputs/0", {"input": "orders", "missing": ["amount"]})
    ]


def test_a_different_artifact_type_stops_the_replay_for_review():
    store = ArtifactStore(uuid4())
    run, issues = start_replay(saved(), given(store, artifact_type=T.RAW_FILE), NOW)
    assert run.state is RunState.NEEDS_REVIEW
    assert [(i.code, i.params) for i in issues] == [
        (R.INPUT_TYPE_MISMATCH, {"input": "orders", "expected": T.TABULAR, "actual": T.RAW_FILE})
    ]


def test_only_a_saved_version_can_be_replayed():
    draft = saved().model_copy(update={"workflow_id": None, "workflow_version": None})
    with pytest.raises(ValueError, match="saved"):
        start_replay(draft, given(ArtifactStore(uuid4())), NOW)


def test_a_replay_with_pinned_versions_gives_identical_output_hashes():
    store, defn = ArtifactStore(uuid4()), saved()
    hashes = []
    for _ in range(2):
        inputs = given(store)
        run, _ = start_replay(defn, inputs, NOW)
        run = approve(run, run.plan_hash, USER, NOW)
        refs = {name: given_input.ref for name, given_input in inputs.items()}
        result = execute(run, REGISTRY, {("pass", 1): Spy()}, store, refs)
        hashes.append({name: ref.sha256 for name, ref in result.outputs.items()})
        assert result.run.state is RunState.SUCCEEDED
    assert hashes[0] == hashes[1]
