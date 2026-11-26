import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  Table,
  type TableColumn,
  type TableRowData,
} from "../../src/components/ui/table";

type Key = "name" | "amount";

const COLUMNS: TableColumn<Key>[] = [
  { key: "name", header: "Name", rowHeader: true },
  { key: "amount", header: "Amount", numeric: true },
];

const ROWS: TableRowData<Key>[] = [
  { id: "1", cells: { name: "Invoice 001", amount: "120.00" } },
  { id: "2", cells: { name: "Invoice 002", amount: "85.50" } },
];

describe.each(["ltr", "rtl"] as const)("Table (dir=%s)", (dir) => {
  it("renders a visible caption and column headers with scope=col", () => {
    render(
      <Table caption="Invoices" columns={COLUMNS} rows={ROWS} dir={dir} />,
    );

    expect(screen.getByText("Invoices")).toBeTruthy();
    expect(
      screen.getByRole("columnheader", { name: "Name" }).getAttribute("scope"),
    ).toBe("col");
    expect(
      screen
        .getByRole("columnheader", { name: "Amount" })
        .getAttribute("scope"),
    ).toBe("col");
  });

  it("renders each row's cells, with a row-header column as scope=row", () => {
    render(
      <Table caption="Invoices" columns={COLUMNS} rows={ROWS} dir={dir} />,
    );

    expect(
      screen
        .getByRole("rowheader", { name: "Invoice 001" })
        .getAttribute("scope"),
    ).toBe("row");
    expect(screen.getByText("Invoice 002")).toBeTruthy();
    expect(screen.getByText("120.00")).toBeTruthy();
    expect(screen.getByText("85.50")).toBeTruthy();
  });

  it("gives a numeric cell dir=ltr so digits read right-aligned on RTL pages too", () => {
    render(
      <Table caption="Invoices" columns={COLUMNS} rows={ROWS} dir={dir} />,
    );

    expect(screen.getByText("120.00").getAttribute("dir")).toBe("ltr");
  });

  it("gives a numeric column's header the same alignment class as its cells", () => {
    render(
      <Table caption="Invoices" columns={COLUMNS} rows={ROWS} dir={dir} />,
    );

    const header = screen.getByRole("columnheader", { name: "Amount" });
    const cell = screen.getByText("120.00");
    expect(header.className).toContain("text-end");
    expect(cell.className).toContain("text-end");
  });

  it("puts dir on the scroll container, not the table", () => {
    render(
      <Table caption="Invoices" columns={COLUMNS} rows={ROWS} dir={dir} />,
    );

    expect(
      screen.getByRole("region", { name: "Invoices" }).getAttribute("dir"),
    ).toBe(dir);
    expect(screen.getByRole("table").getAttribute("dir")).toBeNull();
  });

  it("shows the empty state only when there are no rows and it is not loading", () => {
    render(
      <Table
        caption="Invoices"
        columns={COLUMNS}
        rows={[]}
        emptyState={<p>No invoices yet.</p>}
        dir={dir}
      />,
    );

    expect(screen.getByText("No invoices yet.")).toBeTruthy();
  });

  it("does not show the empty state when there are rows", () => {
    render(
      <Table
        caption="Invoices"
        columns={COLUMNS}
        rows={ROWS}
        emptyState={<p>No invoices yet.</p>}
        dir={dir}
      />,
    );

    expect(screen.queryByText("No invoices yet.")).toBeNull();
  });

  it("shows the loading node instead of rows, and sets aria-busy", () => {
    render(
      <Table
        caption="Invoices"
        columns={COLUMNS}
        rows={ROWS}
        loading={<p>Loading invoices…</p>}
        dir={dir}
      />,
    );

    expect(screen.getByText("Loading invoices…")).toBeTruthy();
    expect(screen.queryByText("Invoice 001")).toBeNull();
    expect(screen.getByRole("table").getAttribute("aria-busy")).toBe("true");
  });

  it("wraps the table in a focusable, labelled scroll region", () => {
    render(
      <Table caption="Invoices" columns={COLUMNS} rows={ROWS} dir={dir} />,
    );

    const region = screen.getByRole("region", { name: "Invoices" });
    expect(region.getAttribute("tabIndex")).toBe("0");
    expect(region.className).toContain("overflow-x-auto");
  });

  it("uses only logical alignment classes, never a physical one", () => {
    const { container } = render(
      <Table caption="Invoices" columns={COLUMNS} rows={ROWS} dir={dir} />,
    );

    for (const re of [
      /\btext-left\b/,
      /\btext-right\b/,
      /\bml-\d/,
      /\bmr-\d/,
      /\bpl-\d/,
      /\bpr-\d/,
    ]) {
      expect(re.test(container.innerHTML)).toBe(false);
    }
  });
});
