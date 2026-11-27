"""Workflow shape limits, enforced by the validator before anything runs (P2.4, S-12).

File count and size limits live in each definition's `ResourcePolicy`, capped by D8.
"""

MAX_NODES = 30
MAX_DEPTH = 10
"""Nodes on the longest path."""
MAX_FAN_IN = 10
MAX_FAN_OUT = 10
