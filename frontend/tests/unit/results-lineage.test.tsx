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
import { afterEach, describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import { ResultsBrowser } from "../../src/components/features/results/results-browser";
import { artifact } from "../msw/handlers/results";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("offset=100"),
}));
afterEach(() => document.documentElement.removeAttribute("dir"));

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("row lineage ($dir)", ({ dir, locale, messages }) => {
  it("renders the whole page, inspects the file row, traps focus and restores it on Escape", async () => {
    document.documentElement.dir = dir;
    setScenario("outputs_preview", "large");
    const member = "<em>orders.csv</em>";
    const request = vi.fn(
      ({ params }: { params: { row?: string | readonly string[] } }) =>
        HttpResponse.json({
          sources: [
            { file_id: "import-1", member_path: member, row: 17, page: 2 },
          ],
          operations: [
            { id: "compare", version: 1 },
            { id: "future.operation", version: 2 },
          ],
          requestedRow: params.row,
        }),
    );
    server.use(
      http.get(
        "/api/v1/workspaces/ws-1/runs/run-1/outputs/:artifact/rows/:row/lineage",
        request,
      ),
    );
    const client = new QueryClient();
    const labels = messages.results;
    render(
      <NextIntlClientProvider locale={locale} messages={messages}>
        <QueryClientProvider client={client}>
          <ResultsBrowser wsId="ws-1" runId="run-1" files={[artifact]} />
        </QueryClientProvider>
      </NextIntlClientProvider>,
    );
    const region = await screen.findByRole("region", { name: labels.preview });
    expect(within(region).getAllByRole("row")).toHaveLength(101);
    const name = labels.lineage.openRow.replace("{row}", "107");
    const opener = screen.getByRole("button", { name });
    expect(request).not.toHaveBeenCalled();
    fireEvent.click(opener.closest("tr")!);
    const dialog = await screen.findByRole("dialog", {
      name: labels.lineage.title,
    });
    expect(dialog.className).toContain("end-0");
    expect(dialog.closest("[dir]")?.getAttribute("dir")).toBe(dir);
    expect(await within(dialog).findByText(member)).toBeTruthy();
    expect(dialog.querySelector("em")).toBeNull();
    expect(
      within(dialog).getByText(messages.operations.compare.title, {
        exact: false,
      }),
    ).toBeTruthy();
    expect(within(dialog).getByText("future.operation")).toBeTruthy();
    expect(request.mock.calls[0][0].params.row).toBe("107");
    opener.focus();
    expect(dialog.contains(document.activeElement)).toBe(true);
    fireEvent.keyDown(document, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    await waitFor(() => expect(document.activeElement).toBe(opener));
  });
});
