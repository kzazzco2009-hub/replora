"""`plan_hash`: the SHA-256 an approval is bound to (P1.4, S-11).

The canonical form is the definition's JSON with sorted keys, no whitespace and UTF-8 text.
Numbers are normalized so that values JSON (and so the browser) can't tell apart hash the same:
an integral float within the safe integer range is written as an integer, so `2.0` and `-0.0`
become `2` and `0`. NaN and infinity are not JSON and are rejected.
"""

import hashlib
import json
from typing import Any

from pydantic import JsonValue

from app.core.workflow import WorkflowDefinition

MAX_SAFE_INTEGER = 2**53 - 1


def _normalized(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalized(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalized(item) for item in value]
    if isinstance(value, float) and value.is_integer() and abs(value) <= MAX_SAFE_INTEGER:
        return int(value)
    return value


def canonical_json(value: JsonValue) -> bytes:
    """The one byte form of a JSON value that `plan_hash` hashes."""
    return json.dumps(
        _normalized(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def plan_hash(definition: WorkflowDefinition) -> str:
    """Lowercase hex SHA-256 of the canonical definition. Any change gives a new hash."""
    return hashlib.sha256(canonical_json(definition.model_dump(mode="json"))).hexdigest()
