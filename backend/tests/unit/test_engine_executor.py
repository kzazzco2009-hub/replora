"""P3.3 in-memory executor: topological order, node by node, outputs stored with lineage (T3.2)."""

import hashlib
from uuid import uuid4

import pytest
from engine_samples import NOW, Spy, diamond, queued
from validator_samples import REGISTRY, definition, node, output

from app.core.artifact_type import ArtifactType as T
from app.core.artifacts import ArtifactLineage
from app.core.engine.executor import execute, topological_order
from app.core.engine.run import PlanHashMismatchError, new_run
from app.core.engine.store import ArtifactStore, Data
from app.core.operations import OperationRef
from app.core.run_state import RunState
from app.core.workflow import InputContract, PortRef

PASS = OperationRef(id="pass", version=1)


def run_it(defn, spy=None):
    spy = spy or Spy()
    store = ArtifactStore(workspace_id=uuid4())
    result = execute(queued(defn), REGISTRY, {("pass", 1): spy}, store, inputs={})
    return result, store, spy


def test_the_order_is_topological_and_stable():
    assert topological_order(diamond()) == ["a", "c", "b", "d"]


def test_each_node_runs_once_after_its_sources():
    result, _, spy = run_it(diamond())
    assert spy.calls == ["a", "c", "b", "d"]
    assert (result.run.state, result.issues) == (RunState.SUCCEEDED, [])


def test_outputs_are_stored_with_content_hash_and_lineage():
    result, store, _ = run_it(diamond())
    final = result.outputs["result"]
    assert store.read(final).content == b"d(b(a())c(a()))"
    assert final.sha256 == hashlib.sha256(b"d(b(a())c(a()))").hexdigest()
    assert (final.type, final.format, final.workspace_id) == (T.TABULAR, "csv", store.workspace_id)
    parents = [result.artifacts["b", "out"].id, result.artifacts["c", "out"].id]
    assert final.lineage == ArtifactLineage(
        run_id=result.run.id, node_id="d", operation=PASS, parents=parents
    )
    assert result.artifacts["a", "out"].lineage.parents == []


def test_workflow_inputs_feed_their_target_ports():
    store = ArtifactStore(workspace_id=uuid4())
    upload = store.put(Data(content=b"x", format="csv"), T.TABULAR, ArtifactLineage())
    feed = InputContract(
        name="f", artifact_type=T.TABULAR, targets=[PortRef(node_id="a", port="in_0")]
    )
    defn = definition([node("a", tag="a")], [], [feed], [output("result", "a", "out", T.TABULAR)])
    result = execute(queued(defn), REGISTRY, {("pass", 1): Spy()}, store, inputs={"f": upload})
    final = result.outputs["result"]
    assert store.read(final).content == b"a(x)"
    assert final.lineage.parents == [upload.id]


def test_a_run_without_a_valid_approval_does_not_execute():
    spy = Spy()
    unapproved = new_run(diamond(), NOW).model_copy(update={"state": RunState.QUEUED})
    with pytest.raises(PlanHashMismatchError):
        execute(unapproved, REGISTRY, {("pass", 1): spy}, ArtifactStore(uuid4()), inputs={})
    assert spy.calls == []
