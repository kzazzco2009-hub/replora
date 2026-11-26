"""The workflow validator (Phase 2): a definition is checked against the operation registry.

It never raises. Every finding is an `Issue` with a stable code (`IssueCode`) and its location:
a path into the definition, and the node when there is one.
"""

from app.core.registry import OperationRegistry
from app.core.validation import ValidationReport
from app.core.validator import structure, types
from app.core.validator.graph import Graph
from app.core.workflow import WorkflowDefinition


def validate(definition: WorkflowDefinition, registry: OperationRegistry) -> ValidationReport:
    """Every error in `definition`. It is valid when there are none."""
    graph = Graph.build(definition, registry)
    errors = [*graph.issues, *structure.check(graph), *types.check(graph)]
    return ValidationReport(valid=not errors, errors=errors, warnings=[])
