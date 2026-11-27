"""§5 registry: the known operations and the server limits (docs/api_contract.md).

Both are public, the same for every user, and cached for an hour. They need no session.
"""

from typing import Any

from fastapi import APIRouter, Request, Response

from app.api.problem import ERROR_RESPONSES
from app.api.v1.operation_models import Limits, OperationContract
from app.core.limits import MAX_DEPTH, MAX_FAN_IN, MAX_FAN_OUT, MAX_NODES
from app.files.service import MAX_FILE_SIZE, MAX_FILES_PER_RUN
from app.ops.registry import REGISTRY

PUBLIC_HOUR = "public, max-age=3600"

CACHED_FOR_AN_HOUR: dict[int | str, dict[str, Any]] = {
    200: {
        "headers": {
            "Cache-Control": {
                "description": "Public: the same for every user",
                "schema": {"type": "string", "example": "public, max-age=3600"},
            }
        }
    },
    501: ERROR_RESPONSES[501],
}

operations = APIRouter(tags=["operations"], responses=CACHED_FOR_AN_HOUR)
limits = APIRouter(tags=["limits"], responses=CACHED_FOR_AN_HOUR)


@operations.get("/operations", name="list")
def list_operations(response: Response) -> list[OperationContract]:
    """Every operation a workflow can use, with its ports and parameter schema."""
    response.headers["Cache-Control"] = PUBLIC_HOUR
    return REGISTRY.list()


@limits.get("/limits", name="get")
def get_limits(request: Request, response: Response) -> Limits:
    """File size, files per run, nodes per workflow and the workspace storage quota."""
    response.headers["Cache-Control"] = PUBLIC_HOUR
    quota = request.app.state.settings.workspace_quota_bytes
    return Limits(max_file_size=MAX_FILE_SIZE, max_files_per_run=MAX_FILES_PER_RUN,
                  max_nodes=MAX_NODES, max_depth=MAX_DEPTH, max_fan_in=MAX_FAN_IN,
                  max_fan_out=MAX_FAN_OUT, workspace_quota=quota)  # fmt: skip
