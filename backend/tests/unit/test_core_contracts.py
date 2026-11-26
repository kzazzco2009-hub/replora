"""P1.1 domain contracts: artifacts, ports and operations are frozen, strict and round-trip."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.v1 import operation_models, output_models
from app.core.artifacts import ArtifactLineage, ArtifactRef, ArtifactType
from app.core.operations import OperationContract, OperationRef, Port

SHA = "a" * 64


def _contract() -> OperationContract:
    return OperationContract(
        id="normalize_columns",
        version=1,
        title_key="operations.normalize_columns",
        inputs=[Port(name="table", artifact_type=ArtifactType.TABULAR, required=True)],
        outputs=[Port(name="table", artifact_type=ArtifactType.TABULAR, required=True)],
        params_schema={"type": "object", "properties": {}},
    )


def _uploaded() -> ArtifactRef:
    return ArtifactRef(
        id=uuid4(),
        type=ArtifactType.RAW_FILE,
        format="csv",
        sha256=SHA,
        workspace_id=uuid4(),
        lineage=ArtifactLineage(),
    )


def _produced() -> ArtifactRef:
    return ArtifactRef(
        id=uuid4(),
        type=ArtifactType.TABULAR,
        format="csv",
        sha256=SHA,
        workspace_id=uuid4(),
        lineage=ArtifactLineage(
            run_id=uuid4(),
            node_id="n1",
            operation=OperationRef(id="parse_csv", version=1),
            parents=[uuid4()],
        ),
    )


MODELS = [_contract, _uploaded, _produced]


def test_there_are_11_artifact_kinds():
    assert len(ArtifactType) == 11


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
    with pytest.raises(ValidationError, match="frozen_instance"):
        model.id = "changed"


@pytest.mark.parametrize("bad", ["A" * 64, "a" * 63, "g" * 64])
def test_sha256_is_64_lowercase_hex(bad):
    with pytest.raises(ValidationError, match="sha256"):
        ArtifactRef.model_validate({**_uploaded().model_dump(), "sha256": bad})


@pytest.mark.parametrize("bad", ["CSV", "", "x" * 17, "c.sv"])
def test_format_is_a_short_lowercase_name(bad):
    with pytest.raises(ValidationError, match="format"):
        ArtifactRef.model_validate({**_uploaded().model_dump(), "format": bad})


@pytest.mark.parametrize(
    "lineage",
    [
        {"node_id": "n1"},
        {"run_id": str(uuid4()), "node_id": "n1"},
        {"parents": [str(uuid4())]},
    ],
)
def test_lineage_is_either_an_upload_or_fully_produced(lineage):
    with pytest.raises(ValidationError, match="lineage"):
        ArtifactLineage.model_validate(lineage)


def test_unknown_artifact_type_is_rejected():
    with pytest.raises(ValidationError):
        Port(name="x", artifact_type="CsvFile", required=True)


def test_api_reuses_the_core_types():
    assert operation_models.ArtifactType is ArtifactType
    assert operation_models.Port is Port
    assert operation_models.OperationContract is OperationContract
    assert output_models.OperationRef is OperationRef
