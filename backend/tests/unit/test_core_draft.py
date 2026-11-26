"""P1.3 planner output and validation reports: frozen, strict, and internally consistent."""

import pytest
from pydantic import ValidationError

from app.api.v1 import draft_models, run_models
from app.core.draft import Explanation, WorkflowDraft
from app.core.operations import OperationRef
from app.core.validation import Issue, ValidationReport
from app.core.workflow import Node, WorkflowDefinition

DEFINITION = WorkflowDefinition(
    nodes=[Node(id="parse", operation=OperationRef(id="parse_csv", version=1))],
    edges=[],
    inputs=[],
    outputs=[],
)
WARNING = Issue(code="COLUMN_RENAMED", path="nodes/0/params/column", node_id="parse")


def _template_draft() -> WorkflowDraft:
    return WorkflowDraft(
        definition=DEFINITION,
        explanation=Explanation(key="templates.reconcile.explain", params={"left": "orders"}),
        warnings=[WARNING],
    )


def _ai_draft() -> WorkflowDraft:
    return WorkflowDraft(
        definition=DEFINITION, explanation=Explanation(text="سأقرأ الملف ثم أطابق")
    )


def _failed_report() -> ValidationReport:
    return ValidationReport(
        valid=False,
        errors=[Issue(code="PORT_UNBOUND", path="nodes/0/inputs/file", node_id="parse")],
        warnings=[WARNING],
    )


MODELS = [_template_draft, _ai_draft, _failed_report, lambda: WARNING]


@pytest.mark.parametrize("make", MODELS)
def test_round_trip_is_identical(make):
    model = make()
    assert type(model).model_validate(model.model_dump()) == model
    assert type(model).model_validate_json(model.model_dump_json()) == model


@pytest.mark.parametrize("make", MODELS)
def test_extra_fields_are_rejected(make):
    model = make()
    with pytest.raises(ValidationError, match="extra_forbidden"):
        type(model).model_validate({**model.model_dump(), "surprise": 1})


@pytest.mark.parametrize("make", MODELS)
def test_models_are_frozen(make):
    model = make()
    field = next(iter(type(model).model_fields))
    with pytest.raises(ValidationError, match="frozen_instance"):
        setattr(model, field, None)


def test_a_draft_has_no_warnings_by_default():
    assert _ai_draft().warnings == []


@pytest.mark.parametrize(
    "explanation",
    [{}, {"key": "k", "text": "t"}, {"text": "t", "params": {"x": 1}}],
)
def test_explanation_is_a_key_with_params_or_a_text(explanation):
    with pytest.raises(ValidationError, match="explanation"):
        Explanation(**explanation)


@pytest.mark.parametrize(
    ("valid", "errors"),
    [(True, [Issue(code="PORT_UNBOUND", path="nodes/0")]), (False, [])],
)
def test_valid_means_no_errors(valid, errors):
    with pytest.raises(ValidationError, match="valid"):
        ValidationReport(valid=valid, errors=errors, warnings=[])


def test_a_report_with_only_warnings_is_valid():
    assert ValidationReport(valid=True, errors=[], warnings=[WARNING]).valid


def test_api_reuses_the_core_types():
    assert draft_models.Explanation is Explanation
    assert draft_models.Issue is Issue
    assert draft_models.ValidationReport is ValidationReport
    assert run_models.Issue is Issue
