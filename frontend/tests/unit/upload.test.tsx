import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { isApiError } from "../../src/lib/api/problem";
import {
  uploadFile,
  useLimits,
  validateBeforeUpload,
  type Limits,
} from "../../src/lib/api/upload";
import { setScenario } from "../msw/scenarios";

function file(name: string, size: number, type = "text/csv"): File {
  return new File([new Uint8Array(size)], name, { type });
}

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
});

describe("useLimits", () => {
  it("resolves GET /limits", async () => {
    const { result } = renderHook(() => useLimits(), { wrapper });

    await waitFor(() => expect(result.current.data).toBeDefined());
    expect(result.current.data).toEqual({
      max_file_size: 52_428_800,
      max_files_per_run: 10,
      max_nodes: 30,
      workspace_quota: 524_288_000,
    });
  });
});

describe("validateBeforeUpload", () => {
  const limits: Limits = {
    max_file_size: 1000,
    max_files_per_run: 2,
    max_nodes: 30,
    workspace_quota: 1_000_000,
  };

  it("passes a file within both limits", () => {
    expect(validateBeforeUpload(file("a.csv", 500), limits, 1)).toBeNull();
  });

  it("flags a file over the size limit", () => {
    expect(validateBeforeUpload(file("a.csv", 1001), limits, 1)).toBe(
      "file_too_large",
    );
  });

  it("flags a selection over the file-count limit", () => {
    expect(validateBeforeUpload(file("a.csv", 500), limits, 3)).toBe(
      "too_many_files",
    );
  });

  it("checks size before count", () => {
    expect(validateBeforeUpload(file("a.csv", 1001), limits, 3)).toBe(
      "file_too_large",
    );
  });
});

describe("uploadFile", () => {
  it("resolves to the ready File after intent -> PUT -> complete", async () => {
    setScenario("files_complete", "ready");
    const result = await uploadFile(file("orders.csv", 10), {
      wsId: "ws-1",
    });

    expect(result.status).toBe("ready");
    expect(result.detected_type).toBe("csv");
  });

  it("resolves (does not throw) to a rejected File with its rejection_code", async () => {
    setScenario("files_complete", "rejected");
    const result = await uploadFile(file("orders.pdf", 10), {
      wsId: "ws-1",
    });

    expect(result.status).toBe("rejected");
    expect(result.rejection_code).toBe("FILE_TYPE_UNSUPPORTED");
  });

  it("reports progress from the PUT", async () => {
    setScenario("files_complete", "ready");
    const fractions: number[] = [];

    await uploadFile(file("orders.csv", 10), {
      wsId: "ws-1",
      onProgress: (fraction) => fractions.push(fraction),
    });

    for (const fraction of fractions) {
      expect(fraction).toBeGreaterThanOrEqual(0);
      expect(fraction).toBeLessThanOrEqual(1);
    }
  });

  it.each([
    ["too_large", "FILE_TOO_LARGE"],
    ["quota_exceeded", "QUOTA_EXCEEDED"],
  ])(
    "rejects with an ApiError mapping to %s when upload-intent returns 413",
    async (scenario, code) => {
      setScenario("files_create_upload_intent", scenario);

      let caught: unknown;
      await uploadFile(file("orders.csv", 10), { wsId: "ws-1" }).catch(
        (error: unknown) => {
          caught = error;
        },
      );

      expect(isApiError(caught) && caught.problem.code).toBe(code);
    },
  );

  it("aborts when the signal is already aborted", async () => {
    setScenario("files_create_upload_intent", "ok");
    const controller = new AbortController();
    controller.abort();

    let caught: unknown;
    await uploadFile(file("orders.csv", 10), {
      wsId: "ws-1",
      signal: controller.signal,
    }).catch((error: unknown) => {
      caught = error;
    });

    expect((caught as { name?: string })?.name).toBe("AbortError");
  });
});
