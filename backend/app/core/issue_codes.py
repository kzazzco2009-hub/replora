"""The stable codes a validation report can carry (P2.6).

Each one is listed in `contracts/error-codes.json` → `workflow_codes`, and the frontend translates
it. A code never changes meaning; a new rule gets a new code.
"""

from enum import StrEnum


class IssueCode(StrEnum):
    OP_UNKNOWN = "OP_UNKNOWN"
    OP_VERSION_INVALID = "OP_VERSION_INVALID"
    NODE_ID_DUPLICATE = "NODE_ID_DUPLICATE"
    NODE_UNKNOWN = "NODE_UNKNOWN"
    PORT_UNKNOWN = "PORT_UNKNOWN"
    PORT_UNBOUND = "PORT_UNBOUND"
    PORT_BOUND_TWICE = "PORT_BOUND_TWICE"
    EDGE_DUPLICATE = "EDGE_DUPLICATE"
    DAG_CYCLE = "DAG_CYCLE"
    PORT_TYPE_MISMATCH = "PORT_TYPE_MISMATCH"
    PARAM_INVALID = "PARAM_INVALID"
