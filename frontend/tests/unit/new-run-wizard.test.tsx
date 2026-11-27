import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { NewRunWizard } from "../../src/components/features/new-run/new-run-wizard";
import messages from "../../messages/en.json";
import { setScenario } from "../msw/scenarios";
import { installSelectJsdomPolyfills } from "./select-jsdom-polyfills";

let restorePolyfills: () => void;

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
  restorePolyfills = installSelectJsdomPolyfills();
});

afterEach(() => {
  restorePolyfills();
});

function renderWizard() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <QueryClientProvider client={client}>
        <NewRunWizard wsId="ws-1" />
      </QueryClientProvider>
    </NextIntlClientProvider>,
  );
}

function pickFiles(files: File[]) {
  const input = document.querySelector('input[type="file"]')!;
  fireEvent.change(input, { target: { files } });
}

describe("NewRunWizard", () => {
  it("starts on Upload, with Next disabled until a file is ready", async () => {
    setScenario("files_complete", "ready");
    renderWizard();
    await waitFor(() => screen.getByText(/Up to 10 files/));

    const next = screen.getByRole("button", { name: "Next: Describe" });
    expect(next.hasAttribute("disabled")).toBe(true);

    pickFiles([
      new File([new Uint8Array(10)], "orders.csv", { type: "text/csv" }),
    ]);

    await waitFor(() => expect(next.hasAttribute("disabled")).toBe(false));
  });

  it("carries the ready file over to Describe as a file-assignment option", async () => {
    setScenario("files_complete", "ready");
    renderWizard();
    await waitFor(() => screen.getByText(/Up to 10 files/));
    pickFiles([
      new File([new Uint8Array(10)], "orders.csv", { type: "text/csv" }),
    ]);
    await waitFor(() =>
      expect(
        screen
          .getByRole("button", { name: "Next: Describe" })
          .hasAttribute("disabled"),
      ).toBe(false),
    );

    fireEvent.click(screen.getByRole("button", { name: "Next: Describe" }));

    fireEvent.click(
      await screen.findByRole("radio", {
        name: /Match orders with payments/,
      }),
    );
    fireEvent.click(screen.getByLabelText("Orders"));
    expect(screen.getByRole("option", { name: "orders.csv" })).toBeTruthy();
  });

  it("going back to Upload keeps the uploaded file in the list", async () => {
    setScenario("files_complete", "ready");
    renderWizard();
    await waitFor(() => screen.getByText(/Up to 10 files/));
    pickFiles([
      new File([new Uint8Array(10)], "orders.csv", { type: "text/csv" }),
    ]);
    await waitFor(() =>
      expect(
        screen
          .getByRole("button", { name: "Next: Describe" })
          .hasAttribute("disabled"),
      ).toBe(false),
    );
    fireEvent.click(screen.getByRole("button", { name: "Next: Describe" }));
    await screen.findByRole("radiogroup");

    fireEvent.click(screen.getByRole("button", { name: "Back" }));

    expect(screen.getByText("orders.csv")).toBeTruthy();
  });
});
