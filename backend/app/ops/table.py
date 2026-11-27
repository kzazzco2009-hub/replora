"""The tabular artifact (P7.1): named columns, rows of text, and where each row came from.

Cells stay text until `normalize` reads them as numbers or dates, so nothing is guessed early.
Each row's lineage names its source file, ZIP member (if any) and row number (P7.4). On the
engine's ports a table travels as canonical JSON (format `json`).
"""

import json
from dataclasses import dataclass, field
from typing import Any

from app.core.engine.store import Data


@dataclass
class Table:
    columns: list[str]
    rows: list[list[str]]
    lineage: list[dict[str, Any]] = field(default_factory=list)

    def to_data(self) -> Data:
        body = {"columns": self.columns, "rows": self.rows, "lineage": self.lineage}
        return Data(json.dumps(body, ensure_ascii=False, sort_keys=True).encode(), "json")

    @classmethod
    def from_data(cls, data: Data) -> Table:
        body = json.loads(data.content)
        return cls(body["columns"], body["rows"], body["lineage"])

    def column(self, name: str) -> int:
        return self.columns.index(name)
