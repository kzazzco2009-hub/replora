"""Export the OpenAPI document to `contracts/openapi.json`.

Usage (from `backend/`):
    uv run python -m app.export_openapi           write the file
    uv run python -m app.export_openapi --check   exit 1 if the committed file has drifted (CI)
"""

import json
import sys
from pathlib import Path

from app.config import REPO_ROOT, Settings
from app.main import create_app

OPENAPI_PATH = REPO_ROOT / "contracts" / "openapi.json"


def render() -> str:
    """Return the OpenAPI document as stable, pretty JSON text."""
    app = create_app(Settings(_env_file=None, app_env="development"))
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def write(path: Path) -> None:
    """Write the OpenAPI document to `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(), encoding="utf-8", newline="\n")


def check(path: Path) -> int:
    """Return 0 if `path` matches the generated document, else 1."""
    if path.is_file() and path.read_text(encoding="utf-8") == render():
        return 0
    print(
        f"{path} is out of date. Run `uv run python -m app.export_openapi` and commit it.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        sys.exit(check(OPENAPI_PATH))
    write(OPENAPI_PATH)
