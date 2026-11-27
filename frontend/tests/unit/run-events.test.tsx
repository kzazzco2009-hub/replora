import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { fetchRunEvents, useRunEvents } from "../../src/lib/api/run-events";
import { cancelRun, progressErrorKey } from "../../src/lib/api/runs";
import { RUN_ID, run } from "../msw/handlers/runs";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

const ws = "ws-1";
const path = `/api/v1/workspaces/${ws}/runs/${RUN_ID}`;
afterEach(() => vi.restoreAllMocks());

it.each(["SUCCEEDED", "PARTIAL", "FAILED", "CANCELLED"])(
  "reads the %s event stream one cursor at a time",
  async (state) => {
    setScenario("runs_events", state);
    const start = await fetchRunEvents(ws, RUN_ID);
    expect(start.events[0]).toMatchObject({ payload: { state: "RUNNING" } });
    const next = await fetchRunEvents(ws, RUN_ID, start.cursor);
    expect(next.events[0]?.seq).toBeGreaterThan(start.cursor!);
    if (state === "PARTIAL") expect(next.events[0]?.type).toBe("warning");
    const end = await fetchRunEvents(ws, RUN_ID, 3);
    expect(end.events).toMatchObject([{ payload: { state } }]);
  },
);

it("ignores unknown and incomplete events and maps rate limiting", async () => {
  const event = { created_at: run.created_at, payload: {} };
  server.use(
    http.get(`${path}/events`, () =>
      HttpResponse.json({
        events: [
          null,
          { ...event, seq: 1, type: "node_started" },
          {
            ...event,
            seq: 2,
            type: "node_finished",
            payload: { warnings: [] },
          },
        ],
        last_seq: 2,
      }),
    ),
  );
  await expect(fetchRunEvents(ws, RUN_ID)).resolves.toEqual({
    events: [],
    cursor: 2,
  });
  server.resetHandlers();
  setScenario("runs_events", "RATE_LIMITED");
  const error = await fetchRunEvents(ws, RUN_ID).catch(
    (error: unknown) => error,
  );
  expect(error).toMatchObject({ retryAfter: "6" });
  expect(progressErrorKey(error)).toBe("errors.problem.RATE_LIMITED");
});

it("posts cancel without an idempotency header", async () => {
  document.cookie = "replora_csrf=test-token";
  server.use(
    http.post(`${path}/cancel`, ({ request }) => {
      expect(request.headers.get("Idempotency-Key")).toBeNull();
      return HttpResponse.json(
        { ...run, state: "CANCEL_REQUESTED" },
        { status: 202 },
      );
    }),
  );
  await expect(cancelRun(ws, RUN_ID)).resolves.toMatchObject({
    state: "CANCEL_REQUESTED",
  });
});

it("pauses while hidden, dedupes by cursor, and stops at NEEDS_REVIEW", async () => {
  let visibility: DocumentVisibilityState = "hidden";
  vi.spyOn(document, "visibilityState", "get").mockImplementation(
    () => visibility,
  );
  const request = vi.fn((after: string | null) => {
    const first = {
      seq: 1,
      created_at: run.created_at,
      type: "state_changed",
      payload: { state: "DRAFT" },
    };
    return HttpResponse.json(
      after === "1"
        ? {
            events: [
              first,
              { ...first, seq: 2, payload: { state: "NEEDS_REVIEW" } },
            ],
            last_seq: 2,
          }
        : { events: [first], last_seq: 1 },
    );
  });
  server.use(
    http.get(`${path}/events`, ({ request: req }) =>
      request(new URL(req.url).searchParams.get("after")),
    ),
  );
  const client = new QueryClient();
  const { result } = renderHook(() => useRunEvents(ws, RUN_ID, "QUEUED"), {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    ),
  });
  expect(result.current.fetchStatus).toBe("idle");
  expect(request).not.toHaveBeenCalled();
  act(() => {
    visibility = "visible";
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await waitFor(() => expect(result.current.data?.state).toBe("NEEDS_REVIEW"), {
    timeout: 2_500,
  });
  expect(request.mock.calls).toEqual([[null], ["1"]]);
  expect(result.current.data?.events.map((event) => event.seq)).toEqual([1, 2]);
  expect(result.current.isEnabled).toBe(false);
});
