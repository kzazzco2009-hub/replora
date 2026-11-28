import { http, HttpResponse } from "msw";
import type { Workflow } from "../../../src/lib/api/workflows";
import { getScenario } from "../scenarios";

export const workflowsCursor = "older+/=workflows";
export const listedWorkflows: Workflow[] = [
  "Daily طلبات",
  "Weekly orders",
  "Month-end",
].map((name, index) => ({
  id: `01937a5e-7f00-7000-8000-00000000060${index + 1}`,
  name,
  latest_version: index + 2,
  created_by: "01937a5e-7f00-7000-8000-000000000001",
  created_at: "2026-11-27T09:00:00Z",
}));

export const workflowsHandlers = [
  http.get("/api/v1/workspaces/:ws_id/workflows", ({ request }) => {
    const scenario = getScenario("workflows_list");
    if (scenario === "RATE_LIMITED") {
      return HttpResponse.json(
        {
          type: "about:blank",
          title: "Rate limited",
          code: scenario,
          status: 429,
          detail: "internal detail",
        },
        { status: 429 },
      );
    }
    const { searchParams } = new URL(request.url);
    const q = searchParams.get("q")?.toLowerCase() ?? "";
    const cursor = searchParams.get("cursor");
    const limit = Number(searchParams.get("limit") ?? 2);
    const matching =
      scenario === "EMPTY"
        ? []
        : listedWorkflows.filter(({ name }) => name.toLowerCase().includes(q));
    return HttpResponse.json({
      items:
        cursor === workflowsCursor
          ? matching.slice(limit)
          : matching.slice(0, limit),
      next_cursor: !cursor && matching.length > limit ? workflowsCursor : null,
    });
  }),
];
