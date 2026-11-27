"""The real operations (P7.2): their contracts, and the handlers that run them.

Handlers turn port data into tables and reports, call the plain functions in `app.ops`, and add
`op@version` to every row's lineage (P7.4). The ids are the ones the TemplatePlanner uses.
"""

import json
from collections.abc import Callable
from typing import Any

from app.core.artifact_type import ArtifactType as T
from app.core.engine.executor import OperationError, Result
from app.core.engine.store import Data
from app.core.operations import OperationContract, Port
from app.core.registry import OperationRegistry
from app.core.validation import Issue
from app.ops import outputs
from app.ops.compare import compare
from app.ops.csv_adapter import parse_csv
from app.ops.json_adapter import parse_json
from app.ops.normalize import normalize
from app.ops.table import Table
from app.ops.zip_adapter import extract_member

TEXT, LIST = {"type": "string"}, {"type": "array", "items": {"type": "string"}}


def _contract(op_id, inputs, outputs_, required=(), **properties) -> OperationContract:
    return OperationContract(
        id=op_id, version=1, title_key=f"operations.{op_id}.title",
        inputs=[Port(name=n, artifact_type=t, required=r) for n, t, r in inputs],
        outputs=[Port(name=n, artifact_type=t, required=True) for n, t in outputs_],
        params_schema={"type": "object", "additionalProperties": False,
                       "required": list(required), "properties": properties},
    )  # fmt: skip


CONTRACTS = [
    _contract("extract_member", [("archive", T.RAW_FILE, True)], [("file", T.RAW_FILE)],
              ["path"], path=TEXT),
    _contract("parse_csv", [("file", T.RAW_FILE, True)], [("table", T.TABULAR)]),
    _contract("parse_json", [("file", T.RAW_FILE, True)], [("table", T.TABULAR)]),
    _contract("normalize", [("table", T.TABULAR, True)], [("table", T.TABULAR)], key=TEXT,
              key_case={"type": "string", "enum": ["upper", "lower", "as_is"]}, numbers=LIST,
              dates=LIST, date_order={"type": "string", "enum": ["DMY", "MDY"]}),
    _contract("map_columns", [("table", T.TABULAR, True)], [("table", T.TABULAR)],
              ["source", "target"], source=LIST, target=LIST),
    _contract("compare", [("left", T.TABULAR, True), ("right", T.TABULAR, True)],
              [("report", T.COMPARISON_REPORT)], ["key", "value"], key=TEXT, value=TEXT,
              tolerance={"type": "string", "pattern": r"^[0-9]+(\.[0-9]+)?$"}),
    _contract("report_csv", [("report", T.COMPARISON_REPORT, True)], [("file", T.OUTPUT_FILE)],
              encoding={"type": "string", "enum": ["utf-8-sig", "utf-8"]}),
    _contract("summary_json", [("report", T.COMPARISON_REPORT, True)], [("file", T.OUTPUT_FILE)]),
    _contract("bundle_zip", [("report", T.OUTPUT_FILE, True), ("summary", T.OUTPUT_FILE, True)],
              [("file", T.OUTPUT_FILE)]),
    _contract("append_rows", [(f"in_{k}", T.TABULAR, k < 2) for k in range(10)],
              [("table", T.TABULAR)]),
    _contract("export_csv", [("table", T.TABULAR, True)], [("file", T.OUTPUT_FILE)],
              encoding={"type": "string", "enum": ["utf-8-sig", "utf-8"]}),
]  # fmt: skip
REGISTRY = OperationRegistry(CONTRACTS)

Handler = Callable[[dict[str, Data], dict[str, Any]], Result]


def _stamp(table: Table, op: str) -> Table:
    lineage = [{**row, "ops": [*row.get("ops", []), f"{op}@1"]} for row in table.lineage]
    return Table(table.columns, table.rows, lineage)


def _table(op: str, table: Table, warnings=()) -> Result:
    return Result({"table": _stamp(table, op).to_data()}, list(warnings))


def _report(data: Data) -> dict[str, Any]:
    return json.loads(data.content)


def _extract(inputs, params) -> Result:
    archive = inputs["archive"]
    content, source = extract_member(archive.content, params["path"], archive.source)
    source = {**source, "ops": [*archive.source.get("ops", []), "extract_member@1"]}
    return Result({"file": Data(content, params["path"].rsplit(".", 1)[-1].lower(), source)})


def _parse(parse: Callable, op: str) -> Handler:
    def handle(inputs, params) -> Result:
        data = inputs["file"]
        source = {k: v for k, v in data.source.items() if k != "ops"}
        table, warnings = parse(data.content, source)
        ops = data.source.get("ops", [])
        table = Table(
            table.columns, table.rows, [{**row, "ops": list(ops)} for row in table.lineage]
        )
        return _table(op, table, warnings)

    return handle


def _normalize(inputs, params) -> Result:
    table = Table.from_data(inputs["table"])
    order = params.get("date_order")
    options = dict(params) | ({"date_orders": dict.fromkeys(params.get("dates", []), order)}
                              if order else {})  # fmt: skip
    try:
        normalized, warnings = normalize(table, options)
    except OperationError as error:
        if error.code != "COLUMN_MISSING":
            raise
        params_ = {"column": error.params["column"], "available": table.columns}
        drift = Issue(code="SCHEMA_DRIFT", path="params", params=params_)
        return Result({"table": table.to_data()}, [drift])
    return _table("normalize", normalized, warnings)


def _map(inputs, params) -> Result:
    mapping = dict(zip(params["source"], params["target"], strict=True))
    return _table("map_columns", outputs.map_columns(Table.from_data(inputs["table"]),
                                                      {"mapping": mapping}))  # fmt: skip


def _compare(inputs, params) -> Result:
    report, warnings = compare(Table.from_data(inputs["left"]), Table.from_data(inputs["right"]),
                               params)  # fmt: skip
    data = Data(json.dumps(report, ensure_ascii=False, sort_keys=True).encode(), "json")
    return Result({"report": data}, warnings)


def _append(inputs, params) -> Result:
    tables = [Table.from_data(inputs[port]) for port in sorted(inputs, key=lambda p: int(p[3:]))]
    columns = tables[0].columns
    if any(table.columns != columns for table in tables[1:]):
        raise OperationError("COLUMNS_DIFFER", columns=[table.columns for table in tables])
    merged = Table(
        columns, [r for t in tables for r in t.rows], [s for t in tables for s in t.lineage]
    )
    return _table("append_rows", merged)


def _export(inputs, params) -> Result:
    table = Table.from_data(inputs["table"])
    rows = [[outputs.escape_cell(cell) for cell in row] for row in [table.columns, *table.rows]]
    text = "".join(",".join(_quote(cell) for cell in row) + "\r\n" for row in rows)
    return Result({"file": Data(text.encode(params.get("encoding", "utf-8-sig")), "csv")})


def _quote(cell: str) -> str:
    if any(ch in cell for ch in ',"\r\n'):
        return '"' + cell.replace('"', '""') + '"'
    return cell


def _report_csv(inputs, params) -> Result:
    return Result({"file": Data(outputs.report_csv(_report(inputs["report"]), params), "csv")})


def _summary(inputs, params) -> Result:
    return Result({"file": Data(outputs.summary_json(_report(inputs["report"]), params), "json")})


def _bundle(inputs, params) -> Result:
    files = {"comparison_report.csv": inputs["report"].content,
             "summary.json": inputs["summary"].content}  # fmt: skip
    return Result({"file": Data(outputs.bundle_zip(files), "zip")})


HANDLERS: dict[tuple[str, int], Handler] = {
    ("extract_member", 1): _extract,
    ("parse_csv", 1): _parse(parse_csv, "parse_csv"),
    ("parse_json", 1): _parse(parse_json, "parse_json"),
    ("normalize", 1): _normalize,
    ("map_columns", 1): _map,
    ("compare", 1): _compare,
    ("report_csv", 1): _report_csv,
    ("summary_json", 1): _summary,
    ("bundle_zip", 1): _bundle,
    ("append_rows", 1): _append,
    ("export_csv", 1): _export,
}  # fmt: skip
