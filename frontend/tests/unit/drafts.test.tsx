import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { isApiError } from "../../src/lib/api/problem";
import { mapFieldErrors } from "../../src/lib/api/field-errors";
import { mapProblem } from "../../src/lib/api/error-messages";
import {
  createDraft,
  useTemplates,
  type DraftCreateBody,
} from "../../src/lib/api/drafts";
import { setScenario } from "../msw/scenarios";

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

function body(overrides: Partial<DraftCreateBody> = {}): DraftCreateBody {
  return {
    file_ids: ["file-1", "file-2"],
    prompt: "",
    planner: "template",
    template_id: "reconcile",
    share_samples: false,
    ...overrides,
  };
}

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
});

describe("useTemplates", () => {
  it("resolves the template list", async () => {
    const { result } = renderHook(() => useTemplates(), { wrapper });

    await waitFor(() => expect(result.current.data).toBeDefined());
    expect(result.current.data?.map((template) => template.id)).toEqual([
      "reconcile",
      "merge",
    ]);
    expect(result.current.data?.[0].required_inputs).toHaveLength(2);
  });
});

describe("createDraft", () => {
  it("resolves the draft and the ETag to send back as If-Match", async () => {
    setScenario("drafts_create", "ok");

    const result = await createDraft(body(), { wsId: "ws-1" });

    expect(result.draft.plan_hash).toBeTruthy();
    expect(result.etag).toBe('"test-etag-1"');
  });

  it.each([
    ["template_id_missing", "template_id", "MISSING"],
    ["template_id_invalid", "template_id", "INVALID"],
    ["file_ids_invalid", "file_ids", "INVALID"],
  ])(
    "maps the %s 422 to a field error on %s (%s)",
    async (scenario, field, code) => {
      setScenario("drafts_create", scenario);

      let caught: unknown;
      await createDraft(body(), { wsId: "ws-1" }).catch((error: unknown) => {
        caught = error;
      });

      expect(isApiError(caught)).toBe(true);
      if (!isApiError(caught)) throw new Error("expected an ApiError");
      const fieldErrors = mapFieldErrors(caught.problem);
      expect(fieldErrors.fields[field]?.messageKey).toBe(
        `errors.validation.${code}`,
      );
    },
  );

  it("falls back to the generic validation message for a per-file code the client doesn't know (no operation_codes catalogue yet)", async () => {
    setScenario("drafts_create", "file_ids_item_invalid");

    let caught: unknown;
    await createDraft(body(), { wsId: "ws-1" }).catch((error: unknown) => {
      caught = error;
    });

    expect(isApiError(caught)).toBe(true);
    if (!isApiError(caught)) throw new Error("expected an ApiError");
    const fieldErrors = mapFieldErrors(caught.problem);
    expect(fieldErrors.fields["file_ids.0"]?.messageKey).toBe(
      "errors.validation.INVALID",
    );
  });

  it.each([
    ["file_not_found", "NOT_FOUND"],
    ["rate_limited", "RATE_LIMITED"],
    ["ai_not_implemented", "NOT_IMPLEMENTED"],
  ])(
    "maps %s through the existing problem mapper to %s",
    async (scenario, code) => {
      setScenario("drafts_create", scenario);

      let caught: unknown;
      await createDraft(body(), { wsId: "ws-1" }).catch((error: unknown) => {
        caught = error;
      });

      expect(isApiError(caught)).toBe(true);
      if (!isApiError(caught)) throw new Error("expected an ApiError");
      expect(caught.problem.code).toBe(code);
      expect(mapProblem(caught.problem).messageKey).toBe(
        `errors.problem.${code}`,
      );
    },
  );
});
