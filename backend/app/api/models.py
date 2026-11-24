"""Base model for API bodies, and cursor pagination (docs/api_contract.md §1)."""

from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    """Unknown fields are rejected (plan P1.7)."""

    model_config = ConfigDict(extra="forbid")


class Page[T](ApiModel):
    """One page of a list. Pass `next_cursor` back as `cursor`; `null` means the last page."""

    items: list[T]
    next_cursor: str | None


Cursor = Annotated[str | None, Query(description="Opaque `next_cursor` from the previous page")]
Limit = Annotated[int, Query(ge=1, le=100)]
