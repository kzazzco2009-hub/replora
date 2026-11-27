import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DescribeStep } from "../../src/components/features/describe/describe-step";
import messages from "../../messages/en.json";
import { setScenario } from "../msw/scenarios";
import { installSelectJsdomPolyfills } from "./select-jsdom-polyfills";

const FILES = [
  { id: "file-orders", displayName: "orders.csv" },
  { id: "file-payments", displayName: "payments.csv" },
];

let restorePolyfills: () => void;

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
  restorePolyfills = installSelectJsdomPolyfills();
});

afterEach(() => {
  restorePolyfills();
});

function renderStep(dir: "ltr" | "rtl" = "ltr") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const onBack = vi.fn();
  const view = render(
    <div dir={dir}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <QueryClientProvider client={client}>
          <DescribeStep wsId="ws-1" files={FILES} onBack={onBack} />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
  return { ...view, onBack };
}

async function chooseTemplate(name: string) {
  fireEvent.click(await screen.findByRole("radio", { name: new RegExp(name) }));
}

function assign(inputLabel: string, fileLabel: string) {
  fireEvent.click(screen.getByLabelText(inputLabel));
  fireEvent.click(screen.getByRole("option", { name: fileLabel }));
}

async function chooseTemplateAndAssignBoth() {
  await chooseTemplate("Match orders with payments");
  assign("Orders", "orders.csv");
  assign("Payments", "payments.csv");
}

describe.each(["ltr", "rtl"] as const)("DescribeStep (dir=%s)", (dir) => {
  it("lists the templates as a radiogroup, cards with a check icon when selected", async () => {
    renderStep(dir);

    const radios = await screen.findAllByRole("radio");
    expect(radios).toHaveLength(2);
    const card = radios[0].closest("div") as HTMLElement;
    const iconBefore = card.querySelector("svg")?.outerHTML;

    fireEvent.click(radios[0]);

    expect(card.querySelector("svg")?.outerHTML).not.toBe(iconBefore);
  });
});

describe("DescribeStep behavior", () => {
  it("shows the right input slots, labelled, once a template is chosen", async () => {
    renderStep();
    await chooseTemplate("Match orders with payments");

    expect(screen.getByLabelText("Orders")).toBeTruthy();
    expect(screen.getByLabelText("Payments")).toBeTruthy();
    expect(
      screen
        .getByRole("button", { name: "Create draft" })
        .hasAttribute("disabled"),
    ).toBe(true);
  });

  it("enables Create draft only once every input has a file, and creates it", async () => {
    setScenario("drafts_create", "ok");
    renderStep();
    await chooseTemplate("Match orders with payments");

    assign("Orders", "orders.csv");
    expect(
      screen
        .getByRole("button", { name: "Create draft" })
        .hasAttribute("disabled"),
    ).toBe(true);

    assign("Payments", "payments.csv");
    expect(
      screen
        .getByRole("button", { name: "Create draft" })
        .hasAttribute("disabled"),
    ).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Create draft" }));

    await waitFor(() => {
      expect(screen.getByText("Draft created")).toBeTruthy();
      expect(
        screen.getByRole("button", { name: "Review" }).hasAttribute("disabled"),
      ).toBe(true);
    });
    expect(screen.getByText("Match orders with payments")).toBeTruthy();
  });

  it("doesn't offer the same file for two inputs", async () => {
    renderStep();
    await chooseTemplate("Match orders with payments");
    assign("Orders", "orders.csv");

    fireEvent.click(screen.getByLabelText("Payments"));

    expect(screen.queryByRole("option", { name: "orders.csv" })).toBeNull();
    expect(screen.getByRole("option", { name: "payments.csv" })).toBeTruthy();
  });

  it.each([
    ["template_id_missing", /This field is required/],
    ["file_ids_item_invalid", /This value isn't valid/], // no operation_codes catalogue yet
    ["file_not_found", /couldn't be found/],
  ])("maps the %s error to %s, never raw detail", async (scenario, text) => {
    setScenario("drafts_create", scenario);
    renderStep();
    await chooseTemplateAndAssignBoth();

    fireEvent.click(screen.getByRole("button", { name: "Create draft" }));

    await waitFor(() => expect(screen.getByText(text)).toBeTruthy());
  });

  it("calls onBack", async () => {
    const { onBack } = renderStep();
    await screen.findByRole("radiogroup");

    fireEvent.click(screen.getByRole("button", { name: "Back" }));

    expect(onBack).toHaveBeenCalled();
  });
});
