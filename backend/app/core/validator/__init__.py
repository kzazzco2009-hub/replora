"""The workflow validator (Phase 2): a definition is checked against the operation registry.

It never raises. Every finding is an `Issue` with a stable code (`IssueCode`) and its location:
a path into the definition, and the node when there is one. Limits are checked first (S-12), and
every check is linear in the size of the definition.
"""

from collections.abc import Sequence

from app.core.registry import OperationRegistry
from app.core.validation import ValidationReport
from app.core.validator import limits, structure, types
from app.core.validator.graph import Graph
from app.core.workflow import WorkflowDefinition


def validate(
    definition: WorkflowDefinition, registry: OperationRegistry, file_sizes: Sequence[int] = ()
) -> ValidationReport:
    """Every error in `definition`. `file_sizes` are the bytes of the files a run would read."""
    graph = Graph.build(definition, registry)
    errors = [
        *limits.check(graph, file_sizes),
        *graph.issues,
        *structure.check(graph),
        *types.check(graph),
    ]
    return ValidationReport(valid=not errors, errors=errors, warnings=[])
