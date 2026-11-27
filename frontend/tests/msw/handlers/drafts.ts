import { http, HttpResponse } from "msw";
import { getScenario } from "../scenarios";

type FixtureCase = { status: number; body: Record<string, unknown> | null };

const TEMPLATES_ERROR_FIXTURES: Record<string, FixtureCase> = {
  not_implemented: {
    status: 501,
    body: {
      type: "about:blank",
      title: "Not Implemented",
      status: 501,
      code: "NOT_IMPLEMENTED",
      correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
    },
  },
};

const TEMPLATES_OK = [
  {
    id: "reconcile",
    title_key: "templates.reconcile.title",
    description_key: "templates.reconcile.description",
    required_inputs: [
      {
        title_key: "templates.reconcile.inputs.0",
        artifact_type: "TabularArtifact",
      },
      {
        title_key: "templates.reconcile.inputs.1",
        artifact_type: "TabularArtifact",
      },
    ],
  },
  {
    id: "merge",
    title_key: "templates.merge.title",
    description_key: "templates.merge.description",
    required_inputs: [
      {
        title_key: "templates.merge.inputs.0",
        artifact_type: "TabularArtifact",
      },
      {
        title_key: "templates.merge.inputs.1",
        artifact_type: "TabularArtifact",
      },
    ],
  },
];

const DRAFT_OK = {
  id: "01937a5e-7f00-7000-8000-000000000301",
  prompt: "",
  planner: "template",
  definition: {
    schema_version: 1,
    nodes: [],
    edges: [],
    inputs: [],
    outputs: [],
    resource_policy: {
      max_files: 10,
      max_file_size: 52_428_800,
      max_node_seconds: 120,
      max_run_seconds: 900,
    },
    review_policy: { on_warning: "review" },
  },
  plan_hash: "0000000000000000000000000000000000000000000000000000000000000000",
  explanation: { key: "templates.reconcile.title", params: {} },
  ai_disclosure: { sent_fields: [], samples_sent: false },
  validation: { valid: true, errors: [], warnings: [] },
  created_at: "2026-11-27T09:00:00Z",
};

const DRAFTS_FIXTURES: Record<string, FixtureCase> = {
  ok: { status: 201, body: DRAFT_OK },
  template_id_missing: {
    status: 422,
    body: {
      type: "about:blank",
      title: "Validation failed",
      status: 422,
      code: "VALIDATION_FAILED",
      errors: [{ path: "body.template_id", code: "MISSING", params: {} }],
    },
  },
  template_id_invalid: {
    status: 422,
    body: {
      type: "about:blank",
      title: "Validation failed",
      status: 422,
      code: "VALIDATION_FAILED",
      errors: [{ path: "body.template_id", code: "INVALID", params: {} }],
    },
  },
  file_ids_invalid: {
    status: 422,
    body: {
      type: "about:blank",
      title: "Validation failed",
      status: 422,
      code: "VALIDATION_FAILED",
      errors: [{ path: "body.file_ids", code: "INVALID", params: {} }],
    },
  },
  file_ids_item_invalid: {
    status: 422,
    body: {
      type: "about:blank",
      title: "Validation failed",
      status: 422,
      code: "VALIDATION_FAILED",
      errors: [
        { path: "body.file_ids.0", code: "FILE_TYPE_MISMATCH", params: {} },
      ],
    },
  },
  file_not_found: {
    status: 404,
    body: {
      type: "about:blank",
      title: "Not Found",
      status: 404,
      code: "NOT_FOUND",
      correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
    },
  },
  rate_limited: {
    status: 429,
    body: {
      type: "about:blank",
      title: "Too Many Requests",
      status: 429,
      code: "RATE_LIMITED",
      correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
    },
  },
  ai_not_implemented: {
    status: 501,
    body: {
      type: "about:blank",
      title: "Not Implemented",
      status: 501,
      code: "NOT_IMPLEMENTED",
      correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
    },
  },
};

/**
 * No `contracts/fixtures/templates|drafts/*.json` exist yet (backend-owned,
 * see `contracts/fixtures/auth/`), so these are inline here, same shape as
 * `tests/msw/handlers/files.ts`.
 */
export const draftsHandlers = [
  http.get("/api/v1/templates", () => {
    const scenario = getScenario("templates_list");
    if (scenario === "ok") return HttpResponse.json(TEMPLATES_OK);
    const { status, body } = TEMPLATES_ERROR_FIXTURES[scenario];
    return HttpResponse.json(body, { status });
  }),
  http.post("/api/v1/workspaces/:ws_id/drafts", () => {
    const { status, body } = DRAFTS_FIXTURES[getScenario("drafts_create")];
    return HttpResponse.json(body, {
      status,
      headers: status === 201 ? { ETag: '"test-etag-1"' } : undefined,
    });
  }),
];
