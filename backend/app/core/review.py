"""Answers to a run's review questions (§7 `resolve`): each answer edits the definition.

An open question is a review issue with `params.options`. Every one must be answered with one of
its options, and the answer sets a parameter of the node that asked. The edited definition has a
new plan_hash, so the run must be approved again.
"""

from collections.abc import Sequence

from app.core.validation import Issue
from app.core.workflow import WorkflowDefinition

ANSWERS = {"DATE_AMBIGUOUS": "date_order"}
"""The node parameter each answerable code sets."""


class AnswerError(ValueError):
    """A choice that answers nothing (`INVALID` at its index), or a question left open."""

    def __init__(self, index: int | None, code: str) -> None:
        self.index, self.code = index, code
        super().__init__(code)


def answer(definition: WorkflowDefinition, issues: Sequence[Issue],
           choices: Sequence[tuple[str, str, object]]) -> WorkflowDefinition:  # fmt: skip
    """The definition with each `(code, path, value)` choice applied to the node that asked."""
    questions = {(i.code, i.path): i for i in issues if "options" in i.params}
    body = definition.model_dump(mode="json")
    nodes = {node["id"]: node for node in body["nodes"]}
    answered = set()
    for index, (code, path, value) in enumerate(choices):
        issue = questions.get((code, path))
        if issue is None or code not in ANSWERS or value not in issue.params["options"]:
            raise AnswerError(index, "INVALID")
        nodes[issue.node_id]["params"][ANSWERS[code]] = value
        answered.add((code, path))
    if answered != set(questions):
        raise AnswerError(None, "MISSING")
    return WorkflowDefinition.model_validate(body)
