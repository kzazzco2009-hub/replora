"""P1.6 domain JSON Schemas and golden fixtures (T1.1, T1.6).

Each `contracts/fixtures/domain/<Name>.json` has `valid`, `invalid` and `invalid_backend_only`
cases. The JSON Schema accepts `valid` and rejects `invalid`. `invalid_backend_only` breaks a
cross-field rule JSON Schema can't express, so only the backend model rejects it.
"""

import json

import pytest
from jsonschema import Draft202012Validator
from pydantic import TypeAdapter, ValidationError

from app.config import REPO_ROOT
from app.export_schemas import SCHEMAS, SCHEMAS_DIR, check, render

FIXTURES_DIR = REPO_ROOT / "contracts" / "fixtures" / "domain"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _cases(group):
    return [
        pytest.param(name, case, value, id=f"{name}-{case}")
        for name in SCHEMAS
        for case, value in _load(FIXTURES_DIR / f"{name}.json").get(group, {}).items()
    ]


def _validator(name):
    return Draft202012Validator(_load(SCHEMAS_DIR / f"{name}.schema.json"))


def test_committed_schemas_match_the_models():
    assert check() == 0


def test_every_schema_has_fixtures_and_the_reverse():
    schemas = {path.name.removesuffix(".schema.json") for path in SCHEMAS_DIR.glob("*.json")}
    fixtures = {path.stem for path in FIXTURES_DIR.glob("*.json")}
    assert schemas == fixtures == set(SCHEMAS)


@pytest.mark.parametrize("name", SCHEMAS)
def test_schemas_are_valid_draft_2020_12(name):
    schema = json.loads(render(name))
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("name", SCHEMAS)
def test_each_schema_has_valid_and_invalid_cases(name):
    fixture = _load(FIXTURES_DIR / f"{name}.json")
    assert fixture["valid"]
    assert fixture["invalid"]
    assert set(fixture) <= {"valid", "invalid", "invalid_backend_only"}


@pytest.mark.parametrize(("name", "case", "value"), _cases("valid"))
def test_valid_fixtures_pass_the_schema_and_round_trip(name, case, value):
    assert not list(_validator(name).iter_errors(value))
    adapter = TypeAdapter(SCHEMAS[name])
    model = adapter.validate_python(value)
    assert adapter.validate_python(adapter.dump_python(model)) == model
    assert adapter.validate_json(adapter.dump_json(model)) == model


@pytest.mark.parametrize(("name", "case", "value"), _cases("invalid"))
def test_invalid_fixtures_fail_the_schema_and_the_model(name, case, value):
    assert list(_validator(name).iter_errors(value))
    with pytest.raises(ValidationError):
        TypeAdapter(SCHEMAS[name]).validate_python(value)


@pytest.mark.parametrize(("name", "case", "value"), _cases("invalid_backend_only"))
def test_cross_field_rules_are_enforced_by_the_model(name, case, value):
    assert not list(_validator(name).iter_errors(value))
    with pytest.raises(ValidationError):
        TypeAdapter(SCHEMAS[name]).validate_python(value)
