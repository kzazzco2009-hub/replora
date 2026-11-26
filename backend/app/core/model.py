"""The base of every domain contract."""

from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Unknown fields are rejected, and an instance never changes after it is built (P1.7)."""

    model_config = ConfigDict(extra="forbid", frozen=True)
