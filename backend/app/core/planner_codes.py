"""The stable codes a planner's draft warnings carry (P3.9).

Each one is listed in `contracts/error-codes.json` → `planner_codes`, and the frontend translates
it. A warning means the planner left a choice to the user instead of guessing.
"""

from enum import StrEnum


class PlannerCode(StrEnum):
    KEY_NOT_FOUND = "KEY_NOT_FOUND"
    KEY_AMBIGUOUS = "KEY_AMBIGUOUS"
    VALUE_NOT_FOUND = "VALUE_NOT_FOUND"
    VALUE_AMBIGUOUS = "VALUE_AMBIGUOUS"
    COLUMNS_DIFFER = "COLUMNS_DIFFER"
