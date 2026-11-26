"""Export the domain JSON Schemas to `contracts/schemas/<Name>.schema.json` (P1.6).

Usage (from `backend/`):
    uv run python -m app.export_schemas           write the files
    uv run python -m app.export_schemas --check   exit 1 if a committed file has drifted (CI)
"""

import json
import sys

from pydantic import TypeAdapter

from app.config import REPO_ROOT
from app.core.artifacts import ArtifactRef
from app.core.draft import WorkflowDraft
from app.core.operations import OperationContract
from app.core.run_state import RunState
from app.core.validation import ValidationReport
from app.core.workflow import WorkflowDefinition

SCHEMAS_DIR = REPO_ROOT / "contracts" / "schemas"
SCHEMAS: dict[str, type] = {
    "ArtifactRef": ArtifactRef,
    "OperationContract": OperationContract,
    "RunState": RunState,
    "ValidationReport": ValidationReport,
    "WorkflowDefinition": WorkflowDefinition,
    "WorkflowDraft": WorkflowDraft,
}


def render(name: str) -> str:
    """Return one schema as stable, pretty JSON text."""
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{name}.schema.json",
        **TypeAdapter(SCHEMAS[name]).json_schema(),
    }
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def write() -> None:
    """Write every schema, and remove files for schemas that no longer exist."""
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in set(SCHEMAS_DIR.glob("*.schema.json")) - _paths():
        stale.unlink()
    for name in SCHEMAS:
        (SCHEMAS_DIR / f"{name}.schema.json").write_text(
            render(name), encoding="utf-8", newline="\n"
        )


def check() -> int:
    """Return 0 if the committed files match the models exactly, else 1."""
    current = set(SCHEMAS_DIR.glob("*.schema.json"))
    if current == _paths() and all(
        (SCHEMAS_DIR / f"{name}.schema.json").read_text(encoding="utf-8") == render(name)
        for name in SCHEMAS
    ):
        return 0
    print(
        f"{SCHEMAS_DIR} is out of date. Run `uv run python -m app.export_schemas` and commit it.",
        file=sys.stderr,
    )
    return 1


def _paths() -> set:
    return {SCHEMAS_DIR / f"{name}.schema.json" for name in SCHEMAS}


if __name__ == "__main__":
    sys.exit(check()) if "--check" in sys.argv[1:] else write()
