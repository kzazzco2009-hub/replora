import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import { RunProgress } from "../../src/components/features/run-progress/run-progress";
import type { Run } from "../../src/lib/api/runs";
import { RUN_ID, run } from "../msw/handlers/runs";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

const path = `/api/v1/workspaces/ws-1/runs/${RUN_ID}`;

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("run actions ($dir)", ({ dir, locale, messages }) => {
  const labels = messages.runProgress;

  beforeEach(() => {
    document.documentElement.dir = dir;
    document.cookie = "replora_csrf=test-token";
    server.use(
      http.get(`${path}/events`, () =>
        HttpResponse.json({ events: [], last_seq: 0 }),
      ),
    );
  });
  afterEach(() => document.documentElement.removeAttribute("dir"));

  function showProgress(state: () => Run["state"]) {
    server.use(
      http.get(path, () => HttpResponse.json({ ...run, state: state() })),
    );
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <NextIntlClientProvider locale={locale} messages={messages}>
        <QueryClientProvider client={client}>
          <RunProgress wsId="ws-1" runId={RUN_ID} />
        </QueryClientProvider>
      </NextIntlClientProvider>,
    );
  }

  async function confirmCancel() {
    fireEvent.click(await screen.findByRole("button", { name: labels.cancel }));
    const dialog = screen.getByRole("dialog", { name: labels.confirmCancel });
    expect(dialog.closest("[dir]")?.getAttribute("dir")).toBe(dir);
    fireEvent.click(
      within(dialog).getByRole("button", { name: labels.cancel }),
    );
  }

  it("disables cancel while pending and shows the confirmed request state", async () => {
    let release!: () => void;
    const pending = new Promise<void>((resolve) => {
      release = resolve;
    });
    server.use(
      http.post(`${path}/cancel`, async () => {
        await pending;
        return HttpResponse.json(
          { ...run, state: "CANCEL_REQUESTED" },
          { status: 202 },
        );
      }),
    );
    showProgress(() => "RUNNING");
    await confirmCancel();
    try {
      await within(screen.getByRole("status")).findByText(
        labels.states.CANCEL_REQUESTED,
      );
      expect(
        screen
          .getByRole("button", { name: labels.cancel })
          .hasAttribute("disabled"),
      ).toBe(true);
    } finally {
      release();
    }
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: labels.cancel })).toBeNull(),
    );
    expect(
      within(screen.getByRole("status")).getByText(
        labels.states.CANCEL_REQUESTED,
      ),
    ).toBeTruthy();
  });

  it.each(["CANCEL_REQUESTED", "CANCELLED", "SUCCEEDED"] as const)(
    "refetches and shows the current %s state on a conflict",
    async (state) => {
      let current: Run["state"] = "QUEUED";
      server.use(
        http.post(`${path}/cancel`, () => {
          current = state;
          return HttpResponse.json(
            {
              type: "about:blank",
              title: "private",
              status: 409,
              code: "INVALID_STATE_TRANSITION",
              detail: "internal detail",
            },
            { status: 409 },
          );
        }),
      );
      showProgress(() => current);
      await confirmCancel();
      const message =
        state === "SUCCEEDED" ? labels.alreadyFinished : labels.states[state];
      expect((await screen.findByRole("alert")).textContent).toBe(message);
      expect(screen.queryByText("internal detail")).toBeNull();
    },
  );

  it("cancels a run that needs review immediately", async () => {
    setScenario("runs_cancel", "NEEDS_REVIEW");
    showProgress(() => "NEEDS_REVIEW");
    await confirmCancel();
    expect(await screen.findByText(labels.outcome.cancelled)).toBeTruthy();
  });

  it.each([
    ["SUCCEEDED", "succeeded"],
    ["PARTIAL", "partial"],
    ["FAILED", "failed"],
    ["CANCELLED", "cancelled"],
    ["EXPIRED", "expired"],
  ] as const)("shows the %s outcome and a next action", async (state, key) => {
    showProgress(() => state);
    expect(await screen.findByText(labels.outcome[key])).toBeTruthy();
    expect(
      screen
        .getByRole("link", { name: messages.nav.newRun })
        .getAttribute("href"),
    ).toBe(`/${locale}/new-run`);
    expect(screen.queryByRole("button", { name: labels.cancel })).toBeNull();
    const results = screen.queryByRole("button", { name: labels.viewResults });
    expect(results?.hasAttribute("disabled") ?? false).toBe(
      state === "SUCCEEDED" || state === "PARTIAL",
    );
  });
});
