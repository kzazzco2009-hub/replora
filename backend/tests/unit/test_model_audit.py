"""P1.7 audit: every model in `app` rejects unknown fields and is frozen (T1.2).

The models are found by walking the `app` package, so a new model is audited without being listed.
"""

import importlib
import pkgutil
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings

import app


def _models() -> list[type[BaseModel]]:
    for module in pkgutil.walk_packages(app.__path__, "app."):
        importlib.import_module(module.name)
    found, todo = set(), [BaseModel]
    while todo:
        for sub in todo.pop().__subclasses__():
            todo.append(sub)
            if sub.__module__.startswith("app.") and not issubclass(sub, BaseSettings):
                found.add(sub)
    return sorted(found, key=lambda model: f"{model.__module__}.{model.__qualname__}")


MODELS = [pytest.param(model, id=model.__qualname__) for model in _models()]


def test_the_walk_finds_the_models():
    names = {param.values[0].__name__ for param in MODELS}
    assert {"WorkflowDefinition", "Run", "ResolveRequest", "Health", "ArtifactRef"} <= names


@pytest.mark.parametrize("model", MODELS)
def test_unknown_fields_are_rejected(model):
    assert model.model_config.get("extra") == "forbid"


@pytest.mark.parametrize("model", MODELS)
def test_models_are_frozen(model):
    assert model.model_config.get("frozen") is True


class _Probe(BaseModel):
    """Stands in for any audited model: the config, not the fields, is what is checked."""

    model_config = app.core.model.ContractModel.model_config
    value: int


def test_the_audited_config_really_rejects_and_freezes():
    probe: Any = _Probe(value=1)
    with pytest.raises(ValidationError, match="extra_forbidden"):
        _Probe.model_validate({"value": 1, "surprise": 2})
    with pytest.raises(ValidationError, match="frozen_instance"):
        probe.value = 2
