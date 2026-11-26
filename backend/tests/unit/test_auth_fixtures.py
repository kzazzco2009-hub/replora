"""B0: `contracts/fixtures/auth/` covers every §2 endpoint and matches the generated contract.

The frontend's MSW handlers serve these fixtures (P9.6), so a fixture that drifts from
`openapi.json` or `error-codes.json` would make the mocks lie.
"""

import json

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from app.config import REPO_ROOT

CONTRACTS = REPO_ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures" / "auth"
OPENAPI = json.loads((CONTRACTS / "openapi.json").read_text(encoding="utf-8"))
CODES = json.loads((CONTRACTS / "error-codes.json").read_text(encoding="utf-8"))
PROBLEM = {"$ref": "#/components/schemas/ProblemDetails"}
AUTH_OPERATIONS = {
    operation["operationId"]: operation
    for operations in OPENAPI["paths"].values()
    for operation in operations.values()
    if operation["tags"] == ["auth"]
}


def scenarios() -> list[tuple[str, str, dict]]:
    return [
        (path.stem, name, scenario)
        for path in sorted(FIXTURES.glob("*.json"))
        for name, scenario in json.loads(path.read_text(encoding="utf-8")).items()
    ]


def validate(body: object, schema: dict) -> None:
    """Validate against an OpenAPI schema; its `#/components/...` refs resolve in OPENAPI."""
    root = schema | {"components": OPENAPI["components"]}
    Draft202012Validator(root, format_checker=FormatChecker()).validate(body)


def test_every_auth_operation_has_a_fixture_file_with_an_ok_scenario():
    files = {path.stem: path for path in FIXTURES.glob("*.json")}

    assert set(files) == set(AUTH_OPERATIONS)
    for name, path in files.items():
        assert "ok" in json.loads(path.read_text(encoding="utf-8")), name


@pytest.mark.parametrize(("operation_id", "name", "scenario"), scenarios())
def test_scenario_matches_the_contract(operation_id, name, scenario):
    responses = AUTH_OPERATIONS[operation_id]["responses"]
    status = scenario["status"]
    body = scenario["body"]

    assert set(scenario) == {"status", "body"}
    assert str(status) in responses, f"{status} is not documented"
    if status >= 400:
        validate(body, PROBLEM)
        assert CODES["problem_codes"][body["code"]]["status"] == status
        assert body["status"] == status
        assert {item["code"] for item in body.get("errors", [])} <= set(CODES["validation_codes"])
    elif body is None:
        assert (
            responses[str(status)].get("content", {}).get("application/json", {}).get("schema", {})
            == {}
        ), "a null body needs a response without a schema"
    else:
        validate(body, responses[str(status)]["content"]["application/json"]["schema"])


def test_the_validator_rejects_a_drifted_body():
    """Guard for the guard: an unknown field must fail, since every model forbids extras."""
    user = json.loads((FIXTURES / "auth_get_me.json").read_text(encoding="utf-8"))["ok"]["body"]

    with pytest.raises(Exception, match="Additional properties"):
        validate(user | {"surprise": 1}, {"$ref": "#/components/schemas/Me"})
