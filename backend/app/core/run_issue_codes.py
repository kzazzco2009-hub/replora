"""The stable codes the engine reports about a run (P3.4).

Each one is listed in `contracts/error-codes.json` → `run_codes`, and the frontend translates it.
Operations may add their own warning codes, for example `LOW_CONFIDENCE`.
"""

from enum import StrEnum


class RunIssueCode(StrEnum):
    NODE_FAILED = "NODE_FAILED"
    NODE_SKIPPED = "NODE_SKIPPED"
    OUTPUT_MISSING = "OUTPUT_MISSING"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    INPUT_TYPE_MISMATCH = "INPUT_TYPE_MISMATCH"
    INPUT_COLUMNS_MISSING = "INPUT_COLUMNS_MISSING"
