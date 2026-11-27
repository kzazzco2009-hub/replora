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
import { beforeEach, describe, expect, it } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import { RunReview } from "../../src/components/features/run-review/run-review";
import { PLAN_HASH, RUN_ID, run } from "../msw/handlers/runs";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

const path = `/api/v1/workspaces/ws-1/runs/${RUN_ID}`;

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
});

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("RunReview ($dir)", ({ dir, locale, messages }) => {
  const labels = messages.runReview;

  function renderReview() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider messages={messages} locale={locale}>
          <QueryClientProvider client={client}>
            <RunReview wsId="ws-1" runId={RUN_ID} />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
  }

  async function confirm() {
    await waitFor(() => {
      expect(
        screen
          .getByRole("button", { name: labels.approve })
          .hasAttribute("disabled"),
      ).toBe(false);
    });
    fireEvent.click(screen.getByRole("button", { name: labels.approve }));
    const dialog = screen.getByRole("dialog", { name: labels.confirmTitle });
    fireEvent.click(
      within(dialog).getByRole("button", { name: labels.approve }),
    );
  }

  it("approves the loaded plan after confirmation", async () => {
    renderReview();
    await confirm();
    expect(await screen.findByText(RUN_ID)).toBeTruthy();
    expect(
      screen.getByRole("link", { name: labels.openRun }).getAttribute("href"),
    ).toBe(`/${locale}/runs/${RUN_ID}`);
  });

  it("requires a reload before approving a changed plan", async () => {
    setScenario("runs_approve", "PLAN_HASH_MISMATCH");
    renderReview();
    await confirm();
    const reload = await screen.findByRole("button", {
      name: labels.reloadPlan,
    });
    expect(
      screen.getByText(messages.errors.problem.PLAN_HASH_MISMATCH),
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: labels.approve })).toBeNull();
    server.use(
      http.get(path, () =>
        HttpResponse.json({
          ...run,
          plan_hash: PLAN_HASH.replaceAll("a", "b"),
        }),
      ),
    );
    fireEvent.click(reload);
    expect(await screen.findByText("bbbbbbbb")).toBeTruthy();
    expect(
      await screen.findByRole("button", { name: labels.approve }),
    ).toBeTruthy();
  });

  it("refetches after an invalid state conflict and explains expiry", async () => {
    setScenario("runs_approve", "INVALID_STATE_TRANSITION");
    let loads = 0;
    server.use(
      http.get(path, () =>
        HttpResponse.json({
          ...run,
          state: loads++ === 0 ? "AWAITING_APPROVAL" : "EXPIRED",
        }),
      ),
    );
    renderReview();
    await confirm();
    expect(await screen.findByText(labels.expired)).toBeTruthy();
    expect(loads).toBe(2);
    expect(screen.queryByRole("button", { name: labels.approve })).toBeNull();
    expect(screen.queryByText("internal detail")).toBeNull();
  });

  it("shows read-only review issues when the run needs further review", async () => {
    setScenario("runs_get", "NEEDS_REVIEW");
    renderReview();
    expect(await screen.findByText(labels.reviewAnswersLater)).toBeTruthy();
    expect(screen.getByRole("heading", { name: labels.issues })).toBeTruthy();
    expect(screen.queryByRole("button", { name: labels.approve })).toBeNull();
  });
});
