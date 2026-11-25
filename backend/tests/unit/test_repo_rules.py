"""P0.8: the `main` ruleset requires exactly the CI jobs that exist, so no merge waits forever."""

import json
import re

from app.config import REPO_ROOT

GITHUB = REPO_ROOT / ".github"


def ci_job_names() -> set[str]:
    """The `name:` of each top-level job (4-space indent) in ci.yml."""
    text = (GITHUB / "workflows" / "ci.yml").read_text(encoding="utf-8")
    return set(re.findall(r"^    name: (.+)$", text, flags=re.MULTILINE))


def ruleset() -> dict:
    return json.loads((GITHUB / "rulesets" / "main.json").read_text(encoding="utf-8"))


def rule(type_: str) -> dict:
    return next(rule for rule in ruleset()["rules"] if rule["type"] == type_)


def test_required_checks_are_real_ci_jobs():
    required = {
        check["context"]
        for check in rule("required_status_checks")["parameters"]["required_status_checks"]
    }

    assert required == ci_job_names() - {"Detect project parts"}


def test_main_needs_one_other_reviewer_and_allows_no_bypass():
    review = rule("pull_request")["parameters"]

    assert review["required_approving_review_count"] == 1
    assert review["dismiss_stale_reviews_on_push"] is True
    assert review["require_code_owner_review"] is False  # single-owner paths would self-block
    assert ruleset()["bypass_actors"] == []
    assert {"deletion", "non_fast_forward"} <= {rule["type"] for rule in ruleset()["rules"]}
