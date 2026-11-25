"""§5 registry: the known operations and the server limits (docs/api_contract.md).

Both are public, the same for every user, and cached for an hour. They need no session.
"""

from typing import Any

from fastapi import APIRouter

from app.api.problem import ERROR_RESPONSES, not_implemented
from app.api.v1.operation_models import Limits, OperationContract

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
def list_operations() -> list[OperationContract]:
    """Every operation a workflow can use, with its ports and parameter schema."""
    raise not_implemented()


@limits.get("/limits", name="get")
def get_limits() -> Limits:
    """File size, files per run, nodes per workflow and the workspace storage quota."""
    raise not_implemented()
