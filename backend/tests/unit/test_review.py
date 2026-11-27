"""§7 resolve: review answers edit the definition (T8.1)."""

import pytest

from app.core.planner.template import Column, FileFacts, plan
from app.core.review import AnswerError, answer
from app.core.validation import Issue

COLUMNS = [Column(name="id", kind="text", unique=True), Column(name="amount", kind="number")]
FILES = [FileFacts(label=name, format="csv", columns=COLUMNS) for name in ("a.csv", "b.csv")]
PIPELINE = plan("reconcile", FILES).definition

ASKED = Issue(code="DATE_AMBIGUOUS", path="nodes/1/rows", node_id="left",
              params={"column": "paid_on", "options": ["DMY", "MDY"]})  # fmt: skip
NOTE = Issue(code="KEY_DUPLICATED", path="nodes/3/rows", node_id="compare", params={"keys": ["A"]})


def test_an_answer_sets_the_askers_parameter_and_changes_the_plan():
    edited = answer(PIPELINE, [ASKED, NOTE], [("DATE_AMBIGUOUS", "nodes/1/rows", "DMY")])

    node = next(n for n in edited.nodes if n.id == "left")
    assert node.params["date_order"] == "DMY"
    assert edited != PIPELINE


@pytest.mark.parametrize(
    "choice",
    [("DATE_AMBIGUOUS", "nodes/1/rows", "YMD"), ("DATE_AMBIGUOUS", "nodes/9/rows", "DMY"),
     ("KEY_DUPLICATED", "nodes/3/rows", "A")],
    ids=["not an option", "no such question", "not a question"],
)  # fmt: skip
def test_a_choice_that_answers_nothing_is_invalid_at_its_index(choice):
    with pytest.raises(AnswerError) as error:
        answer(PIPELINE, [ASKED, NOTE], [("DATE_AMBIGUOUS", "nodes/1/rows", "DMY"), choice])

    assert (error.value.index, error.value.code) == (1, "INVALID")


def test_every_open_question_needs_an_answer():
    second = ASKED.model_copy(update={"path": "nodes/2/rows", "node_id": "right"})

    with pytest.raises(AnswerError) as error:
        answer(PIPELINE, [ASKED, second], [("DATE_AMBIGUOUS", "nodes/1/rows", "MDY")])

    assert (error.value.index, error.value.code) == (None, "MISSING")
