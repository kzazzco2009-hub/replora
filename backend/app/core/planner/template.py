"""The TemplatePlanner (P3.9): deterministic templates filled from file metadata.

This is what MVP users get before the AI planner, and it stays the fallback afterwards. It never
guesses: when a column choice isn't clear, the draft leaves it out and carries a warning, so the
user picks it (and the validator reports the missing parameter).

Columns match when their names are equal after Unicode NFKC and trimming. Matching is
case-sensitive on purpose. Among the candidates, a name hint (`id`, `amount`, `رقم`, `المبلغ`, …)
can settle a tie; it never picks a column on its own.
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from app.core.artifact_type import ArtifactType
from app.core.draft import Explanation, WorkflowDraft
from app.core.model import ContractModel
from app.core.planner_codes import PlannerCode
from app.core.validation import Issue
from app.core.workflow import (
    Edge,
    InputContract,
    Label,
    Node,
    OutputContract,
    PortRef,
    WorkflowDefinition,
)

KEY_HINTS = frozenset({"id", "code", "no", "number", "ref", "رقم", "كود", "معرف", "الرقم"})
VALUE_HINTS = frozenset({"amount", "total", "value", "price", "sum", "مبلغ", "المبلغ", "قيمة",
                         "القيمة", "الإجمالي", "اجمالي", "المجموع"})  # fmt: skip
PARSERS = {"csv": "parse_csv", "json": "parse_json"}


class Column(ContractModel):
    name: str
    kind: Literal["text", "number", "date"]
    unique: bool = False
    """Every non-empty value in the column is different."""


class FileFacts(ContractModel):
    """What the planner knows about one file: its name, format and columns. Never its rows."""

    label: Label
    format: Literal["csv", "json"]
    columns: list[Column]


@dataclass(frozen=True)
class TemplateSpec:
    id: str
    title_key: str
    description_key: str
    required_inputs: tuple[ArtifactType, ...]
    max_inputs: int


TWO_FILES = (ArtifactType.RAW_FILE, ArtifactType.RAW_FILE)
TEMPLATES = {
    "reconcile": TemplateSpec("reconcile", "templates.reconcile.title",
                              "templates.reconcile.description", TWO_FILES, 2),
    "merge": TemplateSpec("merge", "templates.merge.title", "templates.merge.description",
                          TWO_FILES, 10),
}  # fmt: skip


def plan(template_id: str, files: list[FileFacts]) -> WorkflowDraft:
    """The draft for one template. The same files always give the same draft and plan_hash."""
    spec = TEMPLATES[template_id]
    low, high = len(spec.required_inputs), spec.max_inputs
    if not low <= len(files) <= high:
        count = f"{low}" if low == high else f"{low} to {high}"
        raise ValueError(f"{template_id} needs {count} files")
    if template_id == "merge":
        return _merge(files)
    return _reconcile(*files)


def _normal(name: str) -> str:
    return unicodedata.normalize("NFKC", name).strip()


def _hinted(name: str, hints: frozenset[str]) -> bool:
    return any(token in hints for token in re.split(r"[\W_]+", _normal(name).casefold()))


def _shared(left: FileFacts, right: FileFacts, kinds: set[str], unique: bool) -> list[str]:
    """Left-file names of the columns both files have, of those kinds (and unique in both)."""
    right_columns = {_normal(c.name): c for c in right.columns}
    found = []
    for column in left.columns:
        other = right_columns.get(_normal(column.name))
        if other is None or not {column.kind, other.kind} <= kinds:
            continue
        if not unique or (column.unique and other.unique):
            found.append(column.name)
    return found


def _choose(candidates: list[str], hints: frozenset[str], none: PlannerCode,
            ambiguous: PlannerCode, path: str) -> tuple[str | None, list[Issue]]:  # fmt: skip
    if len(candidates) > 1:
        candidates = [name for name in candidates if _hinted(name, hints)] or candidates
    if len(candidates) == 1:
        return candidates[0], []
    if not candidates:
        return None, [Issue(code=none, path=path)]
    return None, [Issue(code=ambiguous, path=path, params={"candidates": candidates})]


def _reconcile(left: FileFacts, right: FileFacts) -> WorkflowDraft:
    key, warnings = _choose(_shared(left, right, {"text", "number"}, unique=True), KEY_HINTS,
                            PlannerCode.KEY_NOT_FOUND, PlannerCode.KEY_AMBIGUOUS,
                            "nodes/2/params/key")  # fmt: skip
    numbers = [name for name in _shared(left, right, {"number"}, unique=False) if name != key]
    value, more = _choose(numbers, VALUE_HINTS, PlannerCode.VALUE_NOT_FOUND,
                          PlannerCode.VALUE_AMBIGUOUS, "nodes/2/params/value")  # fmt: skip
    params = {name: chosen for name, chosen in (("key", key), ("value", value)) if chosen}
    definition = WorkflowDefinition(
        nodes=[_parser("left", left), _parser("right", right),
               Node(id="compare", operation={"id": "compare", "version": 1}, params=params),
               Node(id="report", operation={"id": "report_csv", "version": 1})],
        edges=[_edge("left", "table", "compare", "left"),
               _edge("right", "table", "compare", "right"),
               _edge("compare", "report", "report", "report")],
        inputs=[_input("left_file", left, "left"), _input("right_file", right, "right")],
        outputs=[OutputContract(name="report", artifact_type=ArtifactType.OUTPUT_FILE,
                                source=PortRef(node_id="report", port="file"))],
    )  # fmt: skip
    labels = {"left": left.label, "right": right.label}
    explanation = Explanation(key="plans.reconcile", params={**params, **labels})
    return WorkflowDraft(definition=definition, explanation=explanation, warnings=warnings + more)


def _merge(files: list[FileFacts]) -> WorkflowDraft:
    ids = [f"file_{index}" for index in range(len(files))]
    definition = WorkflowDefinition(
        nodes=[*(_parser(node_id, facts) for node_id, facts in zip(ids, files, strict=True)),
               Node(id="merge", operation={"id": "append_rows", "version": 1}),
               Node(id="export", operation={"id": "export_csv", "version": 1})],
        edges=[*(_edge(node_id, "table", "merge", f"in_{index}")
                 for index, node_id in enumerate(ids)),
               _edge("merge", "table", "export", "table")],
        inputs=[_input(node_id, facts, node_id) for node_id, facts in zip(ids, files, strict=True)],
        outputs=[OutputContract(name="merged", artifact_type=ArtifactType.OUTPUT_FILE,
                                source=PortRef(node_id="export", port="file"))],
    )  # fmt: skip
    explanation = Explanation(key="plans.merge", params={"files": len(files)})
    return WorkflowDraft(definition=definition, explanation=explanation,
                         warnings=_column_drift(files))  # fmt: skip


def _column_drift(files: list[FileFacts]) -> list[Issue]:
    """A `COLUMNS_DIFFER` warning for each file whose columns aren't the first file's."""
    first = {_normal(c.name): c.name for c in files[0].columns}
    warnings = []
    for index, facts in enumerate(files[1:], start=1):
        names = {_normal(c.name): c.name for c in facts.columns}
        missing = [name for normal, name in first.items() if normal not in names]
        extra = [name for normal, name in names.items() if normal not in first]
        if missing or extra:
            params = {"file": facts.label, "missing": missing, "extra": extra}
            warnings.append(Issue(code=PlannerCode.COLUMNS_DIFFER, path=f"inputs/{index}",
                                  params=params))  # fmt: skip
    return warnings


def _parser(node_id: str, facts: FileFacts) -> Node:
    return Node(id=node_id, operation={"id": PARSERS[facts.format], "version": 1})


def _edge(source: str, out: str, target: str, port: str) -> Edge:
    return Edge(source=PortRef(node_id=source, port=out), target=PortRef(node_id=target, port=port))


def _input(name: str, facts: FileFacts, node_id: str) -> InputContract:
    return InputContract(
        name=name, label=facts.label, artifact_type=ArtifactType.RAW_FILE,
        columns=[c.name for c in facts.columns], targets=[PortRef(node_id=node_id, port="file")],
    )  # fmt: skip
