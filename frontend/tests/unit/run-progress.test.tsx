import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import RunProgressPage from "../../src/app/[locale]/(app)/runs/[runId]/page";
import { RUN_ID, run } from "../msw/handlers/runs";
import { server } from "../msw/server";

vi.mock("next/navigation", () => ({ useParams: () => ({ runId: RUN_ID }) }));
vi.mock("@/lib/api/use-me", () => ({
  useMe: () => ({ data: { memberships: [{ id: "ws-1" }] } }),
}));

const path = `/api/v1/workspaces/ws-1/runs/${RUN_ID}`;

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("run progress ($dir)", ({ dir, locale, messages }) => {
  function showProgress() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <RunProgressPage />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
  }

  it("announces run state and derives station states and warnings from events", async () => {
    const ids = ["read", "inspect", "compare", "export"];
    const [read] = ids;
    server.use(
      http.get(path, () =>
        HttpResponse.json({
          ...run,
          state: "QUEUED",
          nodes: [],
          definition: {
            ...run.definition,
            nodes: ids.map((id) => ({ ...run.definition.nodes[0], id })),
          },
        }),
      ),
      http.get(`${path}/events`, () =>
        HttpResponse.json({
          last_seq: 3,
          events: [
            {
              seq: 1,
              created_at: run.created_at,
              type: "state_changed",
              payload: { state: "RUNNING" },
            },
            {
              seq: 2,
              created_at: run.created_at,
              type: "node_finished",
              node_id: read,
              payload: { warnings: [] },
            },
            {
              seq: 3,
              created_at: run.created_at,
              type: "warning",
              payload: {
                issue: {
                  code: "MISSING",
                  path: "",
                  params: {},
                  node_id: "export",
                },
              },
            },
          ],
        }),
      ),
    );
    showProgress();
    await screen.findByText(messages.runProgress.states.RUNNING, undefined, {
      timeout: 3_000,
    });
    expect(screen.getAllByRole("status")).toHaveLength(1);
    expect(screen.getByRole("status").querySelector("svg")).toBeTruthy();
    const rail = within(
      screen.getByRole("list", { name: messages.runReview.pipeline }),
    );
    const stations = rail.getAllByRole("listitem");
    const labels = messages.runProgress.station;
    [labels.done, labels.active, labels.waiting, labels.warning].forEach(
      (label, index) => {
        expect(within(stations[index]).getByText(label)).toBeTruthy();
        expect(
          stations[index].querySelector('bdi[dir="ltr"]')?.textContent,
        ).toBe(ids[index]);
      },
    );
    expect(screen.getByText(messages.errors.validation.MISSING)).toBeTruthy();
  });

  it("shows a pending state and a mapped failure without the problem detail", async () => {
    server.use(
      http.get(path, () =>
        HttpResponse.json(
          {
            type: "about:blank",
            title: "private",
            code: "RATE_LIMITED",
            status: 429,
            detail: "internal detail",
          },
          { status: 429 },
        ),
      ),
    );
    showProgress();
    expect(screen.getByLabelText(messages.runProgress.loading)).toBeTruthy();
    expect(
      await screen.findByText(messages.errors.problem.RATE_LIMITED),
    ).toBeTruthy();
    expect(screen.queryByText("internal detail")).toBeNull();
  });

  it("shows the empty state for a run without stations", async () => {
    server.use(
      http.get(path, () =>
        HttpResponse.json({
          ...run,
          definition: { ...run.definition, nodes: [] },
          nodes: [],
        }),
      ),
    );
    showProgress();
    expect(await screen.findByText(messages.runReview.emptyPlan)).toBeTruthy();
  });
});
