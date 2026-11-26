"""Shared API types: base model, request email, cursor pagination (docs/api_contract.md §1)."""

from typing import Annotated, Any

from fastapi import Query
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)
from pydantic_core import PydanticCustomError


class ApiModel(BaseModel):
    """Unknown fields are rejected, and a body never changes after it is built (P1.7)."""

    model_config = ConfigDict(extra="forbid", frozen=True)


def _email(value: Any, handler: ValidatorFunctionWrapHandler) -> str:
    """Report any bad email as one stable `invalid_email` type (not Pydantic's `value_error`)."""
    try:
        return handler(value)
    except ValidationError as error:
        raise PydanticCustomError("invalid_email", "Not a valid email address") from error


Email = Annotated[EmailStr, WrapValidator(_email)]
"""A request email; every bad value is reported as `INVALID_EMAIL`."""


class Page[T](ApiModel):
    """One page of a list. Pass `next_cursor` back as `cursor`; `null` means the last page."""

    items: list[T]
    next_cursor: str | None


Cursor = Annotated[str | None, Query(description="Opaque `next_cursor` from the previous page")]
Limit = Annotated[int, Query(ge=1, le=100)]
