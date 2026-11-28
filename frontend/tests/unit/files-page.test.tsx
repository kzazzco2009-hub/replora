import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { http } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import FilesPage from "../../src/app/[locale]/(app)/files/page";
import { filesCursor, listedFiles } from "../msw/handlers/files";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

vi.mock("@/lib/api/use-me", () => ({
  useMe: () => ({ data: { memberships: [{ id: "ws-1" }] } }),
}));

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("files page ($dir)", ({ dir, locale, messages }) => {
  const labels = messages.fileList;
  function showFiles() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <FilesPage />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
  }

  it("renders file metadata, follows the opaque cursor, and sends the selected type", async () => {
    const requestQuery = vi.fn();
    server.use(
      http.get("/api/v1/workspaces/ws-1/files", ({ request }) => {
        requestQuery(Object.fromEntries(new URL(request.url).searchParams));
      }),
    );
    showFiles();
    await screen.findByText(listedFiles[0].display_name);
    expect(requestQuery).toHaveBeenLastCalledWith({});
    expect(screen.queryByText(listedFiles[2].display_name)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: labels.more }));
    await screen.findByText(listedFiles[3].display_name);
    expect(requestQuery).toHaveBeenLastCalledWith({ cursor: filesCursor });
    expect(screen.queryByRole("button", { name: labels.more })).toBeNull();

    const format = new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeStyle: "short",
      numberingSystem: "latn",
    });
    for (const file of listedFiles) {
      const name = screen.getByText(file.display_name);
      const row = within(name.closest("tr")!);
      const type = file.detected_type?.toUpperCase() ?? labels.unknown;
      expect(name.tagName).toBe("BDI");
      expect(row.getByText(type).querySelector("svg")).toBeTruthy();
      expect(row.getByText("1.5 KB").getAttribute("dir")).toBe("ltr");
      const date = format.format(new Date(file.created_at));
      expect(row.getByText(date).closest('[dir="ltr"]')).toBeTruthy();
    }
    const filter = screen.getByRole("combobox", { name: labels.filter });
    expect(within(filter).getAllByRole("option")).toHaveLength(4);
    fireEvent.change(filter, { target: { value: "json" } });
    expect(await screen.findByText(listedFiles[2].display_name)).toBeTruthy();
    expect(screen.queryByText(listedFiles[0].display_name)).toBeNull();
    expect(requestQuery).toHaveBeenLastCalledWith({ type: "json" });
  });

  it("shows the empty state", async () => {
    setScenario("files_list", "EMPTY");
    showFiles();
    expect(await screen.findByText(labels.empty)).toBeTruthy();
  });

  it("shows a localized error without problem detail and retries", async () => {
    setScenario("files_list", "RATE_LIMITED");
    showFiles();
    const alert = await screen.findByRole("alert");
    expect(
      within(alert).getByText(messages.errors.problem.RATE_LIMITED),
    ).toBeTruthy();
    expect(screen.queryByText("internal detail")).toBeNull();
    setScenario("files_list", "ok");
    fireEvent.click(
      within(alert).getByRole("button", { name: messages.runReview.retry }),
    );
    expect(await screen.findByText(listedFiles[0].display_name)).toBeTruthy();
  });
});
