import { http, HttpResponse } from "msw";
import type { OutputArtifact, PreviewPage } from "../../../src/lib/api/results";
import { getScenario } from "../scenarios";

export const artifact: OutputArtifact = {
  id: "01937a5e-7f00-7000-8000-000000000501",
  name: "comparison.csv",
  type: "ComparisonReport",
  format: "csv",
  size: 2048,
  row_count: 3,
  created_at: "2026-11-27T09:00:00Z",
};

const columns: PreviewPage["columns"] = [
  { name: "order_id معرّف", type: "string", nullable: false },
  { name: "amount", type: "decimal", nullable: true },
];
const rows: PreviewPage["rows"] = [
  { row: 7, status: "matched", cells: ["O-101", "100.00"] },
  { row: 20, status: "value_diff", cells: ["O-102", "190.00"] },
  { row: 81, status: "missing_left", cells: ["O-103", null] },
];
const list = "/api/v1/workspaces/:ws_id/runs/:run_id/outputs";
const output = `${list}/:artifact_id`;

function failure(scenario: string) {
  const status = Number(scenario);
  if (![404, 409, 422, 429, 501].includes(status)) return;
  return HttpResponse.json(
    {
      type: "about:blank",
      title: "Private",
      status,
      code: status === 429 ? "RATE_LIMITED" : "NOT_FOUND",
      detail: "internal detail",
    },
    { status },
  );
}

export const resultsHandlers = [
  http.get(list, () => {
    const scenario = getScenario("outputs_list");
    return (
      failure(scenario) ??
      HttpResponse.json(scenario === "empty" ? [] : [artifact])
    );
  }),
  http.get(`${output}/preview`, ({ request }) => {
    const scenario = getScenario("outputs_preview");
    const error = failure(scenario);
    if (error) return error;
    if (scenario === "invalid") return HttpResponse.json({ rows: [] });
    const query = new URL(request.url).searchParams;
    const offset = Number(query.get("offset") ?? 0);
    const limit = Number(query.get("limit") ?? 100);
    const q = query.get("q")?.toLowerCase();
    const status = query.get("status");
    const all =
      scenario === "large"
        ? Array.from({ length: 205 }, (_, index) => ({
            ...rows[index % rows.length],
            row: index + 7,
          }))
        : scenario === "unknown"
          ? [{ ...rows[0], status: "duplicate_key" }]
          : scenario === "empty"
            ? []
            : rows;
    const filtered = all.filter(
      (row) =>
        (!status || status === row.status) &&
        (!q ||
          row.cells.some((cell) =>
            String(cell ?? "")
              .toLowerCase()
              .includes(q),
          )),
    );
    return HttpResponse.json({
      columns,
      rows: filtered.slice(offset, offset + limit),
      total: filtered.length,
      offset,
    });
  }),
  http.get(`${output}/rows/:row/lineage`, ({ params }) => {
    const scenario = getScenario("outputs_lineage");
    return (
      failure(scenario) ??
      HttpResponse.json({
        sources: [
          {
            file_id: "input-1",
            member_path: "orders.csv",
            row: Number(params.row),
          },
        ],
        operations: [{ id: "compare", version: 1 }],
      })
    );
  }),
];
