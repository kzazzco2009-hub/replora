import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { expect, it } from "vitest";
import {
  isResultStatus,
  isTabular,
  resultsErrorKey,
  useOutputPreview,
  useOutputs,
  useRowLineage,
} from "../../src/lib/api/results";
import { artifact } from "../msw/handlers/results";
import { RUN_ID } from "../msw/handlers/runs";
import { setScenario } from "../msw/scenarios";

const location = { wsId: "ws-1", runId: RUN_ID, artifactId: artifact.id };
function query<T>(hook: () => T) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return renderHook(hook, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  }).result;
}

it("loads outputs and can distinguish downloadable-only artifacts", async () => {
  const outputs = query(() => useOutputs(location));
  await waitFor(() => expect(outputs.current.data).toEqual([artifact]));
  expect(isTabular(artifact)).toBe(true);
  expect(isTabular({ ...artifact, row_count: null })).toBe(false);
  expect(isTabular({ ...artifact, format: "zip" })).toBe(false);
  expect(isTabular({ ...artifact, type: "RawFile" })).toBe(false);
});

it("handles an empty output list", async () => {
  setScenario("outputs_list", "empty");
  const outputs = query(() => useOutputs(location));
  await waitFor(() => expect(outputs.current.data).toEqual([]));
});

it("uses offset and limit and uses the returned file row for lineage", async () => {
  setScenario("outputs_preview", "large");
  const page = query(() =>
    useOutputPreview(location, { offset: 100, limit: 100 }),
  );
  await waitFor(() => expect(page.current.data?.rows).toHaveLength(100));
  expect(page.current.data).toMatchObject({ total: 205, offset: 100 });
  const row = page.current.data!.rows[0].row;
  expect(row).toBe(107);
  const lineage = query(() => useRowLineage(location, row));
  await waitFor(() => expect(lineage.current.data?.sources[0].row).toBe(107));
});

it("passes the status and text filter to the server", async () => {
  const page = query(() =>
    useOutputPreview(location, { status: "value_diff", q: "O-102" }),
  );
  await waitFor(() =>
    expect(page.current.data).toMatchObject({ total: 1, rows: [{ row: 20 }] }),
  );
});

it("keeps an unfamiliar status safely", async () => {
  setScenario("outputs_preview", "unknown");
  const page = query(() => useOutputPreview(location, {}));
  await waitFor(() =>
    expect(page.current.data?.rows[0].status).toBe("duplicate_key"),
  );
  expect(isResultStatus("duplicate_key")).toBe(false);
});

it.each(["409", "422", "501", "invalid"])(
  "marks preview %s unavailable",
  async (scenario) => {
    setScenario("outputs_preview", scenario);
    const page = query(() => useOutputPreview(location, {}));
    await waitFor(() => expect(page.current.data).toBeNull());
  },
);

it.each(["404", "429"])(
  "exposes a typed %s error for localization",
  async (scenario) => {
    setScenario("outputs_preview", scenario);
    const page = query(() => useOutputPreview(location, {}));
    await waitFor(() => expect(page.current.isError).toBe(true));
    expect(page.current.error).toMatchObject({
      problem: { status: Number(scenario) },
    });
    expect(resultsErrorKey(page.current.error)).not.toContain(
      "internal detail",
    );
    if (scenario === "429")
      expect(resultsErrorKey(page.current.error)).toBe(
        "errors.problem.RATE_LIMITED",
      );
  },
);
