"""Liveness endpoint."""

from importlib.metadata import version
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class Health(BaseModel):
    """Liveness status and the running backend version."""

    status: Literal["ok"]
    version: str


@router.get("/health")
def get_health() -> Health:
    """Report that the API is up, and which version is running."""
    return Health(status="ok", version=version("replora-backend"))
