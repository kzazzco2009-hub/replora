import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { http } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import Home from "../../src/app/[locale]/(app)/page";
import { historyRuns } from "../msw/handlers/runs";
import { listedWorkflows } from "../msw/handlers/workflows";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

vi.mock("@/lib/api/use-me", () => ({
  useMe: () => ({ status: "success", data: { memberships: [{ id: "ws-1" }] } }),
}));

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("home ($dir)", ({ dir, locale, messages }) => {
  const { home, runHistory, workflowList, runProgress, runReview } = messages;

  function showHome() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <Home />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );

    return {
      runs: within(screen.getByRole("region", { name: home.recentRuns })),
      workflows: within(
        screen.getByRole("region", { name: workflowList.caption }),
      ),
    };
  }

  it("loads both previews with limit=5 and renders localized rows and links", async () => {
    const requests = vi.fn();
    server.use(
      http.get("/api/v1/workspaces/ws-1/:list", ({ params, request }) => {
        requests(
          params.list,
          Object.fromEntries(new URL(request.url).searchParams),
        );
      }),
    );
    const { runs, workflows } = showHome();
    expect(
      screen.getByRole("heading", { level: 1, name: home.title }),
    ).toBeTruthy();
    expect(runs.getByRole("status", { name: runHistory.loading })).toBeTruthy();
    expect(
      workflows.getByRole("status", { name: workflowList.loading }),
    ).toBeTruthy();
    expect(
      screen
        .getByRole("link", { name: home.newReconciliation })
        .getAttribute("href"),
    ).toBe(`/${locale}/new-run`);
    expect(
      runs.getByRole("link", { name: home.viewAllRuns }).getAttribute("href"),
    ).toBe(`/${locale}/runs`);
    expect(
      workflows
        .getByRole("link", { name: home.viewAllWorkflows })
        .getAttribute("href"),
    ).toBe(`/${locale}/workflows`);

    await runs.findByText(historyRuns[0].title);
    await workflows.findByText(listedWorkflows[0].name);
    expect(requests).toHaveBeenCalledWith("runs", { limit: "5" });
    expect(requests).toHaveBeenCalledWith("workflows", { limit: "5" });
    expect(requests).toHaveBeenCalledTimes(2);
    const dateFormat = new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeStyle: "short",
      numberingSystem: "latn",
    });
    for (const [index, run] of historyRuns.entries()) {
      const link = runs.getByRole("link", { name: run.title });
      expect(link.getAttribute("href")).toBe(
        `/${locale}/runs/${run.id}${index < 2 ? "/review" : ""}`,
      );
      const row = within(link.closest("li")!);
      expect(
        row.getByText(runProgress.states[run.state]).querySelector("svg"),
      ).toBeTruthy();
      expect(
        row.getByText(dateFormat.format(new Date(run.created_at))).tagName,
      ).toBe("TIME");
    }
    for (const workflow of listedWorkflows) {
      const name = workflows.getByText(workflow.name);
      expect(name.tagName).toBe("BDI");
      expect(name.textContent).toBe(workflow.name);
    }
  });

  it("renders each empty state", async () => {
    setScenario("runs_list", "EMPTY");
    setScenario("workflows_list", "EMPTY");
    const { runs, workflows } = showHome();
    expect(await runs.findByText(runHistory.empty)).toBeTruthy();
    expect(await workflows.findByText(workflowList.empty)).toBeTruthy();
  });

  it.each(["runs", "workflows"] as const)(
    "lets %s fail and retry independently",
    async (list) => {
      const scenario = list === "runs" ? "runs_list" : "workflows_list";
      setScenario(scenario, "RATE_LIMITED");
      const sections = showHome();
      const failing = sections[list];
      const other = sections[list === "runs" ? "workflows" : "runs"];
      const alert = await failing.findByRole("alert");
      expect(
        within(alert).getByText(
          list === "runs" ? home.runsError : home.workflowsError,
        ),
      ).toBeTruthy();
      expect(screen.queryByText("internal detail")).toBeNull();
      expect(
        await other.findByText(
          list === "runs" ? listedWorkflows[0].name : historyRuns[0].title,
        ),
      ).toBeTruthy();

      setScenario(scenario, "ok");
      fireEvent.click(
        within(alert).getByRole("button", { name: runReview.retry }),
      );
      expect(
        await failing.findByText(
          list === "runs" ? historyRuns[0].title : listedWorkflows[0].name,
        ),
      ).toBeTruthy();
      expect(failing.queryByRole("alert")).toBeNull();
    },
  );
});
