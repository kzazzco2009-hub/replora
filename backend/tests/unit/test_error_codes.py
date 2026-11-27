"""contracts/error-codes.json lists every code the API sends; the frontend translates each one."""

import json
from typing import get_args

import pytest

from app.api.problem import FALLBACK_VALIDATION_CODE, VALIDATION_CODES
from app.api.v1.file_models import RejectionCode
from app.config import REPO_ROOT
from app.core.issue_codes import IssueCode


@pytest.fixture(scope="module")
def error_codes() -> dict:
    return json.loads((REPO_ROOT / "contracts" / "error-codes.json").read_text(encoding="utf-8"))


def test_has_the_agreed_sections(error_codes):
    assert set(error_codes) == {
        "problem_codes", "validation_codes", "rejection_codes", "workflow_codes",
    }  # fmt: skip


def test_workflow_codes_are_exactly_the_validator_issue_codes(error_codes):
    assert set(error_codes["workflow_codes"]) == set(IssueCode)
    assert all(entry["description"] for entry in error_codes["workflow_codes"].values())


def test_rejection_codes_are_exactly_the_file_rejection_codes(error_codes):
    assert set(error_codes["rejection_codes"]) == set(get_args(RejectionCode))
    assert all(entry["description"] for entry in error_codes["rejection_codes"].values())


def test_problem_codes_have_a_status_and_a_description(error_codes):
    for code, entry in error_codes["problem_codes"].items():
        assert set(entry) == {"status", "description"}, code
        assert 400 <= entry["status"] <= 599, code
        assert entry["description"], code


def test_validation_codes_are_exactly_what_the_api_emits(error_codes):
    emitted = set(VALIDATION_CODES.values()) | {FALLBACK_VALIDATION_CODE}

    assert set(error_codes["validation_codes"]) == emitted
    assert all(entry["description"] for entry in error_codes["validation_codes"].values())


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("VALIDATION_FAILED", 422),
        ("NOT_IMPLEMENTED", 501),
        ("NOT_FOUND", 404),
        ("METHOD_NOT_ALLOWED", 405),
        ("INTERNAL_ERROR", 500),
        ("MFA_CHALLENGE_INVALID", 401),
        ("PERSONAL_WORKSPACE_UNDELETABLE", 409),
        # §2, agreed in issue #1: 401 only means "no session"; a wrong secret is 400.
        ("UNAUTHENTICATED", 401),
        ("INVALID_CREDENTIALS", 401),
        ("MFA_CODE_INVALID", 400),
        ("PASSWORD_INCORRECT", 400),
        ("TOKEN_INVALID", 400),
        ("CSRF_FAILED", 403),
        ("EMAIL_NOT_VERIFIED", 403),
        ("MFA_ALREADY_ENABLED", 409),
        ("MFA_NOT_ENABLED", 409),
        ("RATE_LIMITED", 429),
        ("FILE_TOO_LARGE", 413),
        ("QUOTA_EXCEEDED", 413),
        # §1 optimistic concurrency on PATCH (drafts, workflows).
        ("PRECONDITION_FAILED", 412),
        ("PRECONDITION_REQUIRED", 428),
        # §7 runs: state rules and idempotency.
        ("DRAFT_INVALID", 422),
        ("PLAN_HASH_MISMATCH", 409),
        ("INVALID_STATE_TRANSITION", 409),
        ("IDEMPOTENCY_KEY_MISMATCH", 409),
        # §8 workflows: versions are immutable, a new one builds on the latest.
        ("BASE_VERSION_STALE", 409),
    ],
)
def test_agreed_problem_codes_are_listed(error_codes, code, status):
    assert error_codes["problem_codes"][code]["status"] == status
