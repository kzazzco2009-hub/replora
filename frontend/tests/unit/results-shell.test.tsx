import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import ResultsPage from "../../src/app/[locale]/(app)/runs/[runId]/results/page";
import { artifact } from "../msw/handlers/results";
import { RUN_ID, run } from "../msw/handlers/runs";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

vi.mock("next/navigation", () => ({ useParams: () => ({ runId: RUN_ID }) }));
vi.mock("@/lib/api/use-me", () => ({
  useMe: () => ({ data: { memberships: [{ id: "ws-1" }] } }),
}));
const path = `/api/v1/workspaces/ws-1/runs/${RUN_ID}`;
const download = `${path}/outputs/${artifact.id}/download`;
const future = "2099-01-01T00:00:00Z";

beforeEach(() =>
  server.use(
    http.get(path, () =>
      HttpResponse.json({
        ...run,
        state: "PARTIAL",
        summary: {
          matched: 2,
          value_diff: 1,
          missing_left: 0,
          missing_right: 0,
        },
      }),
    ),
  ),
);
afterEach(() => vi.restoreAllMocks());

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("results shell ($dir)", ({ dir, locale, messages }) => {
  function show() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <ResultsPage />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
  }

  function links() {
    const followed = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      followed(this.getAttribute("href"), this.rel);
    });
    return followed;
  }

  it("shows the summary and requests an unmodified storage link on click", async () => {
    const url = "https://storage.example.com/file.csv?signature=Ab%2F1";
    const request = vi.fn(() => HttpResponse.json({ url, expires_at: future }));
    server.use(http.get(download, request));
    const followed = links();
    show();
    const button = await screen.findByRole("button", {
      name: new RegExp(artifact.name),
    });
    expect(
      screen.getByText(messages.results.statuses.matched).querySelector("svg"),
    ).toBeTruthy();
    expect(request).not.toHaveBeenCalled();
    fireEvent.click(button);
    await waitFor(() =>
      expect(followed).toHaveBeenCalledExactlyOnceWith(url, "noopener"),
    );
  });

  it("leaves expired links unopened and requests a fresh link on retry", async () => {
    const url = "/api/files/report.csv?token=2";
    const request = vi
      .fn()
      .mockImplementationOnce(() =>
        HttpResponse.json({ url, expires_at: "2001-01-01T00:00:00Z" }),
      )
      .mockImplementation(() => HttpResponse.json({ url, expires_at: future }));
    server.use(http.get(download, request));
    const followed = links();
    show();
    const button = await screen.findByRole("button", {
      name: new RegExp(artifact.name),
    });
    fireEvent.click(button);
    expect(
      await screen.findByText(messages.results.downloadExpired),
    ).toBeTruthy();
    expect(followed).not.toHaveBeenCalled();
    fireEvent.click(button);
    await waitFor(() =>
      expect(followed).toHaveBeenCalledExactlyOnceWith(url, "noopener"),
    );
    expect(request).toHaveBeenCalledTimes(2);
  });

  it("shows an empty output state", async () => {
    setScenario("outputs_list", "empty");
    show();
    expect(await screen.findByText(messages.results.noFiles)).toBeTruthy();
  });

  it("shows a generic error for an unsafe download URL", async () => {
    server.use(
      http.get(download, () =>
        HttpResponse.json({
          url: "javascript:void(0)",
          expires_at: future,
        }),
      ),
    );
    const followed = links();
    show();
    fireEvent.click(
      await screen.findByRole("button", { name: new RegExp(artifact.name) }),
    );
    expect(
      await screen.findByText(messages.results.requestFailed),
    ).toBeTruthy();
    expect(followed).not.toHaveBeenCalled();
  });
});
