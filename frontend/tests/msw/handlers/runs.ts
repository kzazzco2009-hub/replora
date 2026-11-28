import { http, HttpResponse } from "msw";
import type { RunEvent } from "../../../src/lib/api/run-events";
import type { Operation, Run } from "../../../src/lib/api/runs";
import { getScenario, setScenario } from "../scenarios";

export const RUN_ID = "01937a5e-7f00-7000-8000-000000000401";
export const PLAN_HASH = "a".repeat(64);
const issue = {
  code: "MISSING",
  path: "body.file_ids",
  node_id: "read",
  params: {},
};
export const reviewQuestions = ["paid_on تاريخ", "received_on"].map(
  (column) => ({
    code: "DATE_AMBIGUOUS",
    path: `definition.${column}`,
    params: { column, options: ["DMY", "MDY"] },
  }),
);

export const operation: Operation = {
  id: "parse_csv",
  version: 1,
  title_key: "operations.parse_csv.title",
  inputs: [{ name: "file", artifact_type: "RawFile", required: true }],
  outputs: [
    { name: "table", artifact_type: "TabularArtifact", required: true },
  ],
  params_schema: {},
};

export const run: Run = {
  id: RUN_ID,
  state: "AWAITING_APPROVAL",
  plan_hash: PLAN_HASH,
  definition: {
    schema_version: 1,
    nodes: [
      { id: "read", operation: { id: "parse_csv", version: 1 }, params: {} },
    ],
    edges: [],
    inputs: [],
    outputs: [],
    resource_policy: {
      max_files: 10,
      max_file_size: 52428800,
      node_timeout_seconds: 120,
      run_timeout_seconds: 900,
    },
    review_policy: { on_warning: "review" },
  },
  nodes: [
    {
      node_id: "read",
      operation_id: "parse_csv",
      state: "PENDING",
      attempt: 0,
      warnings: [issue],
    },
  ],
  created_at: "2026-11-27T09:00:00Z",
  review_issues: [],
};

const path = "/api/v1/workspaces/:ws_id/runs";
const resolvedRun: Run = {
  ...run,
  plan_hash: "b".repeat(64),
  nodes: [],
};

function problem(status: number, code: string, errors = {}) {
  return HttpResponse.json(
    {
      type: "about:blank",
      title: code,
      status,
      code,
      ...errors,
      detail: "internal detail",
    },
    { status, headers: { "Content-Type": "application/problem+json" } },
  );
}

const eventBase = { created_at: run.created_at };

function eventsFor(scenario: string): RunEvent[] {
  const state =
    scenario === "PARTIAL" || scenario === "FAILED" || scenario === "CANCELLED"
      ? scenario
      : "SUCCEEDED";
  const events: RunEvent[] = [
    {
      ...eventBase,
      seq: 1,
      type: "state_changed",
      payload: { state: "RUNNING" },
    },
  ];
  if (state === "PARTIAL") {
    events.push({ ...eventBase, seq: 2, type: "warning", payload: { issue } });
  }
  if (state === "PARTIAL" || state === "SUCCEEDED") {
    events.push({
      ...eventBase,
      seq: 3,
      type: "node_finished",
      node_id: "read",
      payload: { warnings: state === "PARTIAL" ? [issue] : [] },
    });
  }
  events.push({
    ...eventBase,
    seq: 4,
    type: "state_changed",
    payload: { state },
  });
  return events;
}

export const runsHandlers = [
  http.get("/api/v1/operations", () => HttpResponse.json([operation])),
  http.post(path, () =>
    getScenario("runs_create") === "DRAFT_INVALID"
      ? problem(422, "DRAFT_INVALID", { errors: [issue] })
      : HttpResponse.json(run, { status: 201 }),
  ),
  http.get(`${path}/:run_id`, () => {
    const scenario = getScenario("runs_get");
    if (scenario === "EXPIRED")
      return HttpResponse.json({ ...run, state: "EXPIRED" });
    if (scenario === "NEEDS_REVIEW" || scenario === "REVIEW_QUESTIONS") {
      return HttpResponse.json({
        ...run,
        state: "NEEDS_REVIEW",
        review_issues: scenario === "NEEDS_REVIEW" ? [issue] : reviewQuestions,
      });
    }
    if (scenario === "RESOLVED") return HttpResponse.json(resolvedRun);
    if (scenario === "RATE_LIMITED") return problem(429, "RATE_LIMITED");
    return HttpResponse.json(run);
  }),
  http.post(`${path}/:run_id/approve`, async ({ request }) => {
    const scenario = getScenario("runs_approve");
    if (scenario === "INVALID_STATE_TRANSITION") return problem(409, scenario);
    if (scenario === "VALIDATION_FAILED")
      return problem(422, scenario, { errors: [issue] });
    if (scenario === "RATE_LIMITED") return problem(429, scenario);
    const body = (await request.json()) as { plan_hash: string };
    if (scenario === "PLAN_HASH_MISMATCH" || body.plan_hash !== PLAN_HASH) {
      return problem(409, "PLAN_HASH_MISMATCH");
    }
    return HttpResponse.json({ ...run, state: "QUEUED" }, { status: 202 });
  }),
  http.post(`${path}/:run_id/resolve`, () => {
    const scenario = getScenario("runs_resolve");
    if (scenario === "NOT_IMPLEMENTED") return problem(501, scenario);
    if (
      scenario === "PLAN_HASH_MISMATCH" ||
      scenario === "INVALID_STATE_TRANSITION"
    ) {
      return problem(409, scenario);
    }
    setScenario("runs_get", "RESOLVED");
    return HttpResponse.json(resolvedRun);
  }),
  http.get(`${path}/:run_id/events`, ({ request }) => {
    const scenario = getScenario("runs_events");
    if (scenario === "RATE_LIMITED") {
      const response = problem(429, scenario);
      response.headers.set("Retry-After", "6");
      return response;
    }
    const after = Number(new URL(request.url).searchParams.get("after") ?? 0);
    const events = eventsFor(scenario)
      .filter((event) => event.seq > after)
      .slice(0, 1);
    return HttpResponse.json({ events, last_seq: events.at(-1)?.seq ?? after });
  }),
  http.post(`${path}/:run_id/cancel`, () => {
    const scenario = getScenario("runs_cancel");
    if (scenario === "INVALID_STATE_TRANSITION") return problem(409, scenario);
    return HttpResponse.json(
      {
        ...run,
        state: scenario === "NEEDS_REVIEW" ? "CANCELLED" : "CANCEL_REQUESTED",
      },
      { status: 202 },
    );
  }),
];
