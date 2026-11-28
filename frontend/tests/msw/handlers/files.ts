import { http, HttpResponse } from "msw";
import { getScenario } from "../scenarios";

type FixtureCase = { status: number; body: Record<string, unknown> };

const UPLOAD_INTENT_FIXTURES: Record<string, FixtureCase> = {
  ok: {
    status: 201,
    body: {
      file_id: "01937a5e-7f00-7000-8000-000000000201",
      upload: {
        url: "/mock-storage/01937a5e-7f00-7000-8000-000000000201",
        method: "PUT",
        headers: { "x-mock-storage": "1" },
        expires_at: "2026-11-27T10:00:00Z",
      },
    },
  },
  too_large: {
    status: 413,
    body: {
      type: "about:blank",
      title: "Payload Too Large",
      status: 413,
      code: "FILE_TOO_LARGE",
      correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
    },
  },
  quota_exceeded: {
    status: 413,
    body: {
      type: "about:blank",
      title: "Payload Too Large",
      status: 413,
      code: "QUOTA_EXCEEDED",
      correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
    },
  },
};

const COMPLETE_FIXTURES: Record<string, FixtureCase> = {
  ready: {
    status: 200,
    body: {
      id: "01937a5e-7f00-7000-8000-000000000201",
      display_name: "orders.csv",
      detected_type: "csv",
      size: 1234,
      sha256: "a".repeat(64),
      status: "ready",
      rejection_code: null,
      members: null,
      uploaded_by: "01937a5e-7f00-7000-8000-000000000001",
      created_at: "2026-11-27T09:00:00Z",
      expires_at: "2026-12-27T09:00:00Z",
    },
  },
  rejected: {
    status: 200,
    body: {
      id: "01937a5e-7f00-7000-8000-000000000201",
      display_name: "orders.pdf",
      detected_type: null,
      size: 1234,
      sha256: null,
      status: "rejected",
      rejection_code: "FILE_TYPE_UNSUPPORTED",
      members: null,
      uploaded_by: "01937a5e-7f00-7000-8000-000000000001",
      created_at: "2026-11-27T09:00:00Z",
      expires_at: "2026-12-27T09:00:00Z",
    },
  },
};

const LIMITS_FIXTURE = {
  max_file_size: 52_428_800,
  max_files_per_run: 10,
  max_nodes: 30,
  workspace_quota: 524_288_000,
};

/**
 * No `contracts/fixtures/files/*.json` exist yet (that directory is
 * backend-owned, see `contracts/fixtures/auth/`), so these cases are
 * inline here instead, following the same scenario-keyed shape.
 */
export const filesHandlers = [
  http.post("/api/v1/workspaces/:ws_id/files/upload-intent", () => {
    const { status, body } =
      UPLOAD_INTENT_FIXTURES[getScenario("files_create_upload_intent")];
    return HttpResponse.json(body, { status });
  }),
  http.put("/mock-storage/:id", () => new HttpResponse(null, { status: 200 })),
  http.post("/api/v1/workspaces/:ws_id/files/:file_id/complete", () => {
    const scenario = getScenario("files_complete");
    const { status, body } =
      COMPLETE_FIXTURES[scenario === "ready_json" ? "ready" : scenario];
    if (scenario === "ready_json") {
      return HttpResponse.json(
        { ...body, display_name: "orders.json", detected_type: "json" },
        { status },
      );
    }
    return HttpResponse.json(body, { status });
  }),
  http.get("/api/v1/limits", () => HttpResponse.json(LIMITS_FIXTURE)),
];
