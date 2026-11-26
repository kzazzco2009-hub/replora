"""The stable codes a validation report can carry (P2.6).

Each one is listed in `contracts/error-codes.json` → `workflow_codes`, and the frontend translates
it. A code never changes meaning; a new rule gets a new code.
"""

from enum import StrEnum


class IssueCode(StrEnum):
    OP_UNKNOWN = "OP_UNKNOWN"
    OP_VERSION_INVALID = "OP_VERSION_INVALID"
