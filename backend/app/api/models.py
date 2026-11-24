"""Base model for API request and response bodies."""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    """Unknown fields are rejected (plan P1.7)."""

    model_config = ConfigDict(extra="forbid")
