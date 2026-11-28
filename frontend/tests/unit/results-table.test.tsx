import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { useSyncExternalStore } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import { ResultsBrowser } from "../../src/components/features/results/results-browser";
import { artifact } from "../msw/handlers/results";
import { setScenario } from "../msw/scenarios";

function subscribe(notify: () => void) {
  window.addEventListener("popstate", notify);
  return () => window.removeEventListener("popstate", notify);
}
vi.mock("next/navigation", () => ({
  useSearchParams: () =>
    new URLSearchParams(useSyncExternalStore(subscribe, () => location.search)),
}));
afterEach(() => {
  vi.restoreAllMocks();
  history.replaceState(null, "", "/");
});

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("results table ($dir)", ({ dir, locale, messages }) => {
  function show() {
    const push = history.pushState.bind(history);
    vi.spyOn(history, "pushState").mockImplementation((...args) => {
      push(...args);
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    const client = new QueryClient();
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <ResultsBrowser wsId="ws-1" runId="run-1" files={[artifact]} />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
  }

  it("paginates, debounces search, and restores the query on Back", async () => {
    setScenario("outputs_preview", "large");
    show();
    const labels = messages.results;
    const next = await screen.findByRole("button", { name: labels.next });
    expect(screen.getByText("order_id معرّف").tagName).toBe("BDI");
    expect(screen.getAllByText("100.00")[0].getAttribute("dir")).toBe("ltr");
    fireEvent.click(next);
    expect(location.search).toBe("?offset=100");
    const search = screen.getByRole<HTMLInputElement>("searchbox");
    fireEvent.change(search, { target: { value: "O-102" } });
    expect(location.search).toBe("?offset=100");
    await waitFor(() => expect(location.search).toBe("?q=O-102"));
    await screen.findAllByText("O-102");
    expect(screen.getByRole("status").textContent).toBe(
      labels.count.replace("{count}", "68"),
    );
    fireEvent.keyDown(
      screen.getByRole("tab", { name: labels.statuses.matched }),
      { key: "Enter" },
    );
    expect(new URLSearchParams(location.search).get("status")).toBe("matched");
    expect(await screen.findByText(labels.noRows)).toBeTruthy();
    history.back();
    await waitFor(() => expect(location.search).toBe("?q=O-102"));
    expect(search.value).toBe("O-102");
  });

  it("labels duplicate keys and filters the preview to those rows", async () => {
    setScenario("outputs_preview", "duplicate");
    show();
    const statuses = messages.results.statuses;
    const tab = screen.getByRole("tab", { name: statuses.duplicate_key });
    expect(tab.querySelector("svg")).not.toBeNull();
    const chip = await screen.findByText(statuses.duplicate_key, {
      selector: "td span",
    });
    expect(chip.querySelector("svg")).not.toBeNull();
    expect(screen.getByText("O-101")).toBeTruthy();

    fireEvent.keyDown(tab, { key: "Enter" });

    expect(new URLSearchParams(location.search).get("status")).toBe(
      "duplicate_key",
    );
    await screen.findByText("O-104");
    expect(screen.queryByText("O-101")).toBeNull();
  });
});
