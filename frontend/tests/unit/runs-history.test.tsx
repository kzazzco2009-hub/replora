import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { http } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import RunsPage from "../../src/app/[locale]/(app)/runs/page";
import { historyCursor, historyRuns } from "../msw/handlers/runs";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

vi.mock("@/lib/api/use-me", () => ({
  useMe: () => ({ data: { memberships: [{ id: "ws-1" }] } }),
}));

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("runs history ($dir)", ({ dir, locale, messages }) => {
  const labels = messages.runHistory;
  const stateLabels = messages.runProgress.states;

  function showHistory() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <RunsPage />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
  }

  it("renders localized runs, follows the next cursor, and filters from the first page", async () => {
    const requestQuery = vi.fn();
    server.use(
      http.get("/api/v1/workspaces/ws-1/runs", ({ request }) => {
        requestQuery(Object.fromEntries(new URL(request.url).searchParams));
      }),
    );
    showHistory();
    await screen.findByText(historyRuns[0].title);
    expect(requestQuery).toHaveBeenLastCalledWith({});
    expect(screen.queryByText(historyRuns[2].title)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: labels.more }));
    await screen.findByText(historyRuns[3].title);
    expect(requestQuery).toHaveBeenLastCalledWith({ cursor: historyCursor });
    expect(screen.queryByRole("button", { name: labels.more })).toBeNull();

    const format = new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeStyle: "short",
      numberingSystem: "latn",
    });
    for (const [index, run] of historyRuns.entries()) {
      const title = screen.getByText(run.title);
      const id = screen.getByText(run.id);
      expect(title.matches('bdi[dir="ltr"]')).toBe(true);
      expect(id.matches('bdi[dir="ltr"]')).toBe(true);
      const href = `/${locale}/runs/${run.id}${index < 2 ? "/review" : ""}`;
      expect(id.closest("a")?.getAttribute("href")).toBe(href);
      const row = within(title.closest("tr")!);
      expect(
        row.getByText(stateLabels[run.state]).querySelector("svg"),
      ).toBeTruthy();
      const date = format.format(new Date(run.finished_at ?? run.created_at));
      expect(row.getByText(date).closest('bdi[dir="ltr"]')).toBeTruthy();
    }

    const filter = screen.getByRole("combobox", { name: labels.filter });
    expect(within(filter).getAllByRole("option")).toHaveLength(13);
    fireEvent.change(filter, { target: { value: "SUCCEEDED" } });
    expect(await screen.findByText(historyRuns[3].title)).toBeTruthy();
    expect(screen.queryByText(historyRuns[0].title)).toBeNull();
    expect(requestQuery).toHaveBeenLastCalledWith({ state: "SUCCEEDED" });
  });

  it("shows the empty state", async () => {
    setScenario("runs_list", "EMPTY");
    showHistory();
    expect(await screen.findByText(labels.empty)).toBeTruthy();
  });

  it("shows a localized error without problem detail and retries", async () => {
    setScenario("runs_list", "RATE_LIMITED");
    showHistory();
    const alert = await screen.findByRole("alert");
    expect(
      within(alert).getByText(messages.errors.problem.RATE_LIMITED),
    ).toBeTruthy();
    expect(screen.queryByText("internal detail")).toBeNull();
    setScenario("runs_list", "ok");
    fireEvent.click(
      within(alert).getByRole("button", { name: messages.runReview.retry }),
    );
    expect(await screen.findByText(historyRuns[0].title)).toBeTruthy();
  });
});
