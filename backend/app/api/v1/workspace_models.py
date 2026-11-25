"""Workspace shapes shared across sections (docs/api_contract.md §3)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from app.api.models import ApiModel

Role = Literal["owner", "admin", "member", "viewer"]


class Workspace(ApiModel):
    """A workspace the current user belongs to, with their role in it."""

    id: UUID
    name: str
    role: Role
    created_at: datetime
