"""Replay a pinned workflow version on new inputs (P3.7).

The new files are checked against the version's input contracts: the artifact type must be the
same, and every expected column must still be there (extra columns are fine). A mismatch stops the
run as NEEDS_REVIEW with the issues. Otherwise it awaits approval like any run (S-11).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from app.core.artifacts import ArtifactRef
from app.core.engine.run import Run, new_run, transition
from app.core.run_issue_codes import RunIssueCode
from app.core.run_state import RunAction
from app.core.validation import Issue
from app.core.workflow import InputContract, WorkflowDefinition


@dataclass(frozen=True)
class ReplayInput:
    """A new file for one workflow input, and the columns found in it."""

    ref: ArtifactRef
    columns: list[str]


def start_replay(
    definition: WorkflowDefinition, inputs: Mapping[str, ReplayInput], now: datetime
) -> tuple[Run, list[Issue]]:
    """A run of a saved version on `inputs` (by input name), and why it needs review, if it does."""
    if definition.workflow_version is None:
        raise ValueError("only a saved workflow version can be replayed")
    issues = [found for index, contract in enumerate(definition.inputs)
              for found in _mismatches(index, contract, inputs[contract.name])]  # fmt: skip
    run = transition(new_run(definition, now), RunAction.VALIDATE, now)
    action = RunAction.REQUEST_REVIEW if issues else RunAction.REQUEST_APPROVAL
    return transition(run, action, now), issues


def _mismatches(index: int, contract: InputContract, given: ReplayInput) -> list[Issue]:
    path, name = f"inputs/{index}", contract.name
    if given.ref.type is not contract.artifact_type:
        params = {"input": name, "expected": contract.artifact_type, "actual": given.ref.type}
        return [Issue(code=RunIssueCode.INPUT_TYPE_MISMATCH, path=path, params=params)]
    missing = [column for column in contract.columns if column not in given.columns]
    if missing:
        params = {"input": name, "missing": missing}
        return [Issue(code=RunIssueCode.INPUT_COLUMNS_MISSING, path=path, params=params)]
    return []
