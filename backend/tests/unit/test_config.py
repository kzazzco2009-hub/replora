"""S-02: configuration comes from the environment, and secrets never leak."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app

FAKE_KEY = "sk-or-v1-not-a-real-key"


def make_settings(**env: str) -> Settings:
    """Settings from explicit values only, never from the developer's real `.env`."""
    return Settings(_env_file=None, **env)


def test_unknown_app_env_is_rejected():
    with pytest.raises(ValidationError) as excinfo:
        make_settings(app_env="staging-typo")

    [error] = excinfo.value.errors()
    assert error["loc"] == ("app_env",)
    assert error["type"] == "literal_error"


def test_secret_is_not_exposed_in_repr_or_dump():
    settings = make_settings(openrouter_api_key=FAKE_KEY)

    assert FAKE_KEY not in repr(settings)
    assert FAKE_KEY not in str(settings.model_dump())
    assert settings.openrouter_api_key.get_secret_value() == FAKE_KEY


def test_settings_read_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")

    assert make_settings().app_env == "test"


def test_blank_value_from_env_example_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("APP_ENV", "")

    assert make_settings().app_env == "development"


def test_production_refuses_to_start_without_its_secrets():
    with pytest.raises(ValidationError, match="openrouter_api_key"):
        make_settings(app_env="production")


def test_production_refuses_to_start_with_debug_on():
    with pytest.raises(ValidationError, match="debug"):
        make_settings(app_env="production", openrouter_api_key=FAKE_KEY, debug="true")


def test_refusal_never_echoes_a_secret():
    with pytest.raises(ValidationError) as excinfo:
        make_settings(app_env="production", openrouter_api_key=FAKE_KEY, debug="true")

    assert "input_value" not in str(excinfo.value)
    assert FAKE_KEY[:4] not in str(excinfo.value)


def test_development_needs_no_secrets_and_may_debug():
    settings = make_settings(app_env="development", debug="true")

    assert settings.debug is True
    assert create_app(settings).debug is True


def test_api_docs_are_disabled_in_production():
    client = TestClient(
        create_app(make_settings(app_env="production", openrouter_api_key=FAKE_KEY))
    )

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_api_docs_are_served_in_development():
    client = TestClient(create_app(make_settings(app_env="development")))

    assert client.get("/docs").status_code == 200
