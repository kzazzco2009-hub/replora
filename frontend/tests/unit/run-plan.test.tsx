import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import {
  operationIds,
  operationTitleKey,
} from "../../src/components/features/run-review/operation-labels";
import { RunPlan } from "../../src/components/features/run-review/run-plan";
import { run } from "../msw/handlers/runs";

const ids = [
  "extract_member",
  "parse_csv",
  "parse_json",
  "normalize",
  "map_columns",
  "compare",
  "report_csv",
  "summary_json",
  "bundle_zip",
  "append_rows",
  "export_csv",
] as const;

it("has exactly the canonical operation labels in both locales", () => {
  expect(operationIds).toEqual(ids);
  for (const messages of [ar, en]) {
    expect(Object.keys(messages.operations).sort()).toEqual([...ids].sort());
    for (const id of ids) {
      expect(operationTitleKey(id)).toBe(`operations.${id}.title`);
      expect(messages.operations[id].title.trim()).toBeTruthy();
    }
  }
});

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("RunPlan ($dir)", ({ dir, locale, messages }) => {
  it("lists localized steps in dependency order with ports and warnings", async () => {
    const first = run.definition.nodes[0];
    const result = {
      ...run,
      definition: {
        ...run.definition,
        nodes: [
          {
            ...first,
            id: "second",
            operation: { id: "unknown-raw-id", version: 1 },
          },
          first,
        ],
        edges: [
          {
            source: { node_id: first.id, port: "table" },
            target: { node_id: "second", port: "file" },
          },
        ],
      },
    };
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <RunPlan run={result} />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );

    const rail = await screen.findByRole("list", {
      name: messages.runReview.pipeline,
    });
    expect(rail.closest("[dir]")?.getAttribute("dir")).toBe(dir);
    const cards = within(rail).getAllByRole("article");
    expect(
      within(cards[0]).getByRole("heading", {
        name: messages.operations.parse_csv.title,
      }),
    ).toBeTruthy();
    expect(within(cards[0]).getByText("file")).toBeTruthy();
    expect(within(cards[0]).getByText("table")).toBeTruthy();
    expect(
      within(cards[0]).getByText(messages.errors.validation.MISSING),
    ).toBeTruthy();
    expect(
      within(cards[1]).getByRole("heading", {
        name: messages.runReview.unknownOperation,
      }),
    ).toBeTruthy();
    expect(rail.textContent).not.toContain("unknown-raw-id");
  });
});
