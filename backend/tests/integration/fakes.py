"""Test-only fake adapters and the MockPlanner (P3.8). Nothing under `app/` may import this.

The pipeline: a ZIP holds a CSV and a JSON file. Each branch is parsed into a table, the two
tables are compared on a key, and the comparison is rendered as a CSV report. A table is the
canonical JSON `{"columns": [...], "rows": [[...], ...]}`.
"""

import csv
import io
import json
import zipfile
from dataclasses import dataclass

from app.core.artifact_type import ArtifactType as T
from app.core.draft import Explanation, WorkflowDraft
from app.core.engine.executor import Result
from app.core.engine.store import Data
from app.core.operations import OperationContract, Port
from app.core.registry import OperationRegistry
from app.core.workflow import Edge, InputContract, Node, OutputContract, PortRef, WorkflowDefinition


def _op(op_id, inputs, outputs, **params_schema) -> OperationContract:
    return OperationContract(
        id=op_id, version=1, title_key=f"operations.{op_id}.title",
        inputs=[Port(name=n, artifact_type=t, required=True) for n, t in inputs],
        outputs=[Port(name=n, artifact_type=t, required=True) for n, t in outputs],
        params_schema={"type": "object", **params_schema},
    )  # fmt: skip


REGISTRY = OperationRegistry([
    _op("fake_unzip", [("archive", T.RAW_FILE)], [("csv", T.RAW_FILE), ("json", T.RAW_FILE)]),
    _op("fake_parse_csv", [("file", T.RAW_FILE)], [("table", T.TABULAR)]),
    _op("fake_parse_json", [("file", T.RAW_FILE)], [("table", T.TABULAR)]),
    _op("fake_compare", [("left", T.TABULAR), ("right", T.TABULAR)],
        [("report", T.COMPARISON_REPORT)], required=["key", "value"],
        properties={"key": {"type": "string"}, "value": {"type": "string"}}),
    _op("fake_render", [("report", T.COMPARISON_REPORT)], [("file", T.OUTPUT_FILE)]),
])  # fmt: skip


def _table(columns, rows) -> Data:
    return Data(json.dumps({"columns": columns, "rows": rows}).encode(), "json")


def unzip(inputs, params) -> Result:
    with zipfile.ZipFile(io.BytesIO(inputs["archive"].content)) as archive:
        names = archive.namelist()
        member = {ext: next(n for n in names if n.endswith(f".{ext}")) for ext in ("csv", "json")}
        return Result({ext: Data(archive.read(name), ext) for ext, name in member.items()})


def parse_csv(inputs, params) -> Result:
    header, *rows = csv.reader(io.StringIO(inputs["file"].content.decode("utf-8")))
    return Result({"table": _table(header, rows)})


def parse_json(inputs, params) -> Result:
    records = json.loads(inputs["file"].content)
    columns = list(records[0])
    return Result({"table": _table(columns, [[str(r[c]) for c in columns] for r in records])})


def compare(inputs, params) -> Result:
    key, value = params["key"], params["value"]
    left, right = (_by_key(inputs[side].content, key, value) for side in ("left", "right"))
    lines = [[k, _status(left.get(k), right.get(k)), left.get(k, ""), right.get(k, "")]
             for k in sorted(left.keys() | right.keys())]  # fmt: skip
    return Result({"report": Data(json.dumps(lines).encode(), "json")})


def _by_key(content: bytes, key: str, value: str) -> dict[str, str]:
    table = json.loads(content)
    k, v = table["columns"].index(key), table["columns"].index(value)
    return {row[k]: row[v] for row in table["rows"]}


def _status(left: str | None, right: str | None) -> str:
    if left is None or right is None:
        return "only_right" if left is None else "only_left"
    return "match" if left == right else "mismatch"


def render(inputs, params) -> Result:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["key", "status", "left", "right"])
    writer.writerows(json.loads(inputs["report"].content))
    return Result({"file": Data(out.getvalue().encode(), "csv")})


HANDLERS = {
    ("fake_unzip", 1): unzip,
    ("fake_parse_csv", 1): parse_csv,
    ("fake_parse_json", 1): parse_json,
    ("fake_compare", 1): compare,
    ("fake_render", 1): render,
}


def _edge(source: str, out: str, target: str, port: str) -> Edge:
    return Edge(source=PortRef(node_id=source, port=out), target=PortRef(node_id=target, port=port))


PIPELINE = WorkflowDefinition(
    nodes=[
        Node(id="unzip", operation={"id": "fake_unzip", "version": 1}),
        Node(id="orders", operation={"id": "fake_parse_csv", "version": 1}),
        Node(id="payments", operation={"id": "fake_parse_json", "version": 1}),
        Node(id="compare", operation={"id": "fake_compare", "version": 1},
             params={"key": "order_id", "value": "amount"}),
        Node(id="render", operation={"id": "fake_render", "version": 1}),
    ],
    edges=[_edge("unzip", "csv", "orders", "file"), _edge("unzip", "json", "payments", "file"),
           _edge("orders", "table", "compare", "left"),
           _edge("payments", "table", "compare", "right"),
           _edge("compare", "report", "render", "report")],
    inputs=[InputContract(name="bundle", artifact_type=T.RAW_FILE,
                          targets=[PortRef(node_id="unzip", port="archive")])],
    outputs=[OutputContract(name="report", artifact_type=T.OUTPUT_FILE,
                            source=PortRef(node_id="render", port="file"))],
)  # fmt: skip


@dataclass(frozen=True)
class MockPlanner:
    """Returns the same draft for any task. Test-only: users get the TemplatePlanner (P3.9)."""

    draft: WorkflowDraft = WorkflowDraft(
        definition=PIPELINE, explanation=Explanation(key="plans.mock.reconcile_bundle")
    )

    def plan(self, task: str, files: list[str]) -> WorkflowDraft:
        return self.draft
