"""Sample operations and definition builders for the validator tests (Phase 2)."""

from typing import Any

from app.core.artifact_type import ArtifactType as T
from app.core.operations import OperationContract, Port
from app.core.registry import OperationRegistry
from app.core.workflow import Edge, InputContract, Node, OutputContract, PortRef, WorkflowDefinition

FAN = 12  # `pass` has more optional inputs than the fan-in limit, for the limit tests.


def op(op_id: str, inputs: list[Port], outputs: list[Port], **params_schema: Any):
    return OperationContract(
        id=op_id,
        version=1,
        title_key=f"operations.{op_id}.title",
        inputs=inputs,
        outputs=outputs,
        params_schema={"type": "object", **params_schema},
    )


REGISTRY = OperationRegistry(
    [
        op("parse_csv", [Port(name="file", artifact_type=T.RAW_FILE, required=True)],
           [Port(name="table", artifact_type=T.TABULAR, required=True)]),
        op("extract_text", [Port(name="file", artifact_type=T.RAW_FILE, required=True)],
           [Port(name="text", artifact_type=T.TEXT_DOCUMENT, required=True)]),
        op("reconcile",
           [Port(name="left", artifact_type=T.TABULAR, required=True),
            Port(name="right", artifact_type=T.TABULAR, required=True)],
           [Port(name="report", artifact_type=T.COMPARISON_REPORT, required=True)],
           required=["key"], additionalProperties=False,
           properties={"key": {"type": "string", "x-replora-widget": "column"},
                       "tolerance": {"type": "string", "pattern": "^[0-9]+(\\.[0-9]+)?$"},
                       "mode": {"type": "string", "enum": ["exact", "fuzzy"]}}),
        op("pass", [Port(name=f"in_{k}", artifact_type=T.TABULAR, required=False)
                    for k in range(FAN)],
           [Port(name="out", artifact_type=T.TABULAR, required=True)]),
    ]
)  # fmt: skip


def node(node_id: str, op_id: str = "pass", version: int = 1, **params: Any) -> Node:
    return Node(id=node_id, operation={"id": op_id, "version": version}, params=params)


def edge(source: str, target: str, source_port: str = "out", target_port: str = "in_0") -> Edge:
    return Edge(
        source=PortRef(node_id=source, port=source_port),
        target=PortRef(node_id=target, port=target_port),
    )


def definition(nodes, edges=(), inputs=(), outputs=(), **policies) -> WorkflowDefinition:
    return WorkflowDefinition(
        nodes=list(nodes), edges=list(edges), inputs=list(inputs), outputs=list(outputs), **policies
    )


def file_input(name: str, node_id: str, port: str = "file") -> InputContract:
    return InputContract(
        name=name, artifact_type=T.RAW_FILE, targets=[PortRef(node_id=node_id, port=port)]
    )


def output(name: str, node_id: str, port: str, artifact_type=T.COMPARISON_REPORT):
    return OutputContract(
        name=name, artifact_type=artifact_type, source=PortRef(node_id=node_id, port=port)
    )


def reconcile_workflow() -> WorkflowDefinition:
    """The first real pipeline: two CSVs reconciled into a comparison report."""
    return definition(
        [node("orders", "parse_csv"), node("payments", "parse_csv"),
         node("compare", "reconcile", key="order_id")],
        [edge("orders", "compare", "table", "left"), edge("payments", "compare", "table", "right")],
        [file_input("orders_file", "orders"), file_input("payments_file", "payments")],
        [output("report", "compare", "report")],
    )  # fmt: skip


def codes(report) -> list[str]:
    return [issue.code for issue in report.errors]
