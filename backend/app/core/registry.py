"""The operation registry: every operation a workflow may use, by `(id, version)` (P2.1).

A params schema must stay inside the subset the frontend renders as a form
(docs/api_contract.md §5): an object whose properties are a string (with an optional `enum` or
`pattern`), an integer, a boolean or an array of strings. No `oneOf`, `anyOf`, `allOf` or `$ref`.
"""

from collections.abc import Iterable
from typing import Any

from app.core.issue_codes import IssueCode
from app.core.operations import OperationContract

FIELD_TYPES = {"string", "integer", "boolean", "array"}
BANNED_KEYWORDS = {"oneOf", "anyOf", "allOf", "not", "$ref", "$defs", "if", "then", "else"}


class RegistryError(LookupError):
    """A registry rule was broken. `code` and `params` go into an `Issue` or a problem."""

    def __init__(self, code: str, **params: Any) -> None:
        self.code = code
        self.params = params
        super().__init__(f"{code} {params}")


class OperationRegistry:
    """Known operation contracts. Read-only once the app has started."""

    def __init__(self, contracts: Iterable[OperationContract] = ()) -> None:
        self._contracts: dict[tuple[str, int], OperationContract] = {}
        for contract in contracts:
            self.register(contract)

    def register(self, contract: OperationContract) -> None:
        """Add a contract. Its `(id, version)` must be new and its params schema in the subset."""
        key = (contract.id, contract.version)
        where = {"operation": contract.id, "version": contract.version}
        if contract.version < 1:
            raise RegistryError(IssueCode.OP_VERSION_INVALID, **where)
        if key in self._contracts:
            raise RegistryError("OP_DUPLICATE", **where)
        if not _in_subset(contract.params_schema):
            raise RegistryError("OP_PARAMS_SCHEMA_INVALID", operation=contract.id)
        self._contracts[key] = contract

    def get(self, op_id: str, version: int) -> OperationContract:
        """The contract, or `OP_UNKNOWN` / `OP_VERSION_INVALID`."""
        if (op_id, version) in self._contracts:
            return self._contracts[op_id, version]
        if known := self.versions(op_id):
            raise RegistryError(
                IssueCode.OP_VERSION_INVALID, operation=op_id, version=version, known=known
            )
        raise RegistryError(IssueCode.OP_UNKNOWN, operation=op_id, version=version)

    def versions(self, op_id: str) -> list[int]:
        """The registered versions of one operation, oldest first."""
        return sorted(version for known, version in self._contracts if known == op_id)

    def list(self) -> list[OperationContract]:
        """Every contract, by id then version (for `GET /operations`)."""
        return [self._contracts[key] for key in sorted(self._contracts)]


def _in_subset(schema: dict[str, Any]) -> bool:
    if schema.get("type") != "object" or _has_banned(schema):
        return False
    return all(_field_ok(field) for field in schema.get("properties", {}).values())


def _field_ok(field: dict[str, Any]) -> bool:
    if field.get("type") not in FIELD_TYPES:
        return False
    if field["type"] == "array":
        return field.get("items") == {"type": "string"}
    return "enum" not in field or field["type"] == "string"


def _has_banned(value: Any) -> bool:
    if isinstance(value, dict):
        return bool(BANNED_KEYWORDS & value.keys()) or any(map(_has_banned, value.values()))
    if isinstance(value, list):
        return any(map(_has_banned, value))
    return False
