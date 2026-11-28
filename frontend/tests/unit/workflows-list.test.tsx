import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { http } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import WorkflowsPage from "../../src/app/[locale]/(app)/workflows/page";
import { listedWorkflows, workflowsCursor } from "../msw/handlers/workflows";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

vi.mock("@/lib/api/use-me", () => ({
  useMe: () => ({ data: { memberships: [{ id: "ws-1" }] } }),
}));
afterEach(() => {
  vi.useRealTimers();
});

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("saved workflows ($dir)", ({ dir, locale, messages }) => {
  const labels = messages.workflowList;
  function showWorkflows() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <WorkflowsPage />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
  }

  function recordQueries() {
    const record = vi.fn();
    server.use(
      http.get("/api/v1/workspaces/ws-1/workflows", ({ request }) => {
        record(Object.fromEntries(new URL(request.url).searchParams));
      }),
    );
    return record;
  }

  it("renders workflow metadata and follows the next cursor", async () => {
    const requests = recordQueries();
    showWorkflows();
    const [first, , older] = listedWorkflows;
    const name = await screen.findByText(first.name);
    expect(name.tagName).toBe("BDI");
    const row = within(name.closest("tr")!);
    expect(
      row.getByText(String(first.latest_version)).getAttribute("dir"),
    ).toBe("ltr");
    const date = new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeStyle: "short",
      numberingSystem: "latn",
    }).format(new Date(first.created_at));
    expect(row.getByText(date).closest('[dir="ltr"]')).toBeTruthy();
    expect(screen.queryByText(older.name)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: labels.more }));
    expect(await screen.findByText(older.name)).toBeTruthy();
    expect(requests).toHaveBeenLastCalledWith({ cursor: workflowsCursor });
    expect(screen.queryByRole("button", { name: labels.more })).toBeNull();
  });

  it("debounces q and distinguishes a search with no matches", async () => {
    const requests = recordQueries();
    showWorkflows();
    await screen.findByText(listedWorkflows[0].name);
    const input = screen.getByRole("searchbox", { name: labels.search });
    vi.useFakeTimers();
    fireEvent.change(input, { target: { value: "  Month-end " } });
    await act(() => vi.advanceTimersByTimeAsync(299));
    expect(requests.mock.calls).toEqual([[{}]]);
    act(() => {
      vi.advanceTimersByTime(1);
      vi.useRealTimers();
    });

    expect(await screen.findByText(listedWorkflows[2].name)).toBeTruthy();
    expect(requests).toHaveBeenLastCalledWith({ q: "Month-end" });
    vi.useFakeTimers();
    fireEvent.change(input, { target: { value: "missing workflow" } });
    act(() => {
      vi.advanceTimersByTime(300);
      vi.useRealTimers();
    });
    expect(await screen.findByText(labels.noResults)).toBeTruthy();
    expect(requests).toHaveBeenLastCalledWith({ q: "missing workflow" });
    expect(screen.queryByText(labels.empty)).toBeNull();
  });

  it("shows the empty state before a search", async () => {
    setScenario("workflows_list", "EMPTY");
    showWorkflows();
    expect(await screen.findByText(labels.empty)).toBeTruthy();
  });

  it("shows a localized error without problem detail and retries", async () => {
    setScenario("workflows_list", "RATE_LIMITED");
    showWorkflows();
    const alert = await screen.findByRole("alert");
    expect(
      within(alert).getByText(messages.errors.problem.RATE_LIMITED),
    ).toBeTruthy();
    expect(screen.queryByText("internal detail")).toBeNull();
    setScenario("workflows_list", "ok");
    fireEvent.click(
      within(alert).getByRole("button", { name: messages.runReview.retry }),
    );
    expect(await screen.findByText(listedWorkflows[0].name)).toBeTruthy();
  });
});
