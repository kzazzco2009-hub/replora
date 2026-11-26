import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Sheet, type SheetProps } from "../../src/components/ui/sheet";

describe.each(["ltr", "rtl"] as const)("Sheet (dir=%s)", (dir) => {
  // RadixDialog.Portal renders into document.body, outside the <div dir>
  // wrapper below, so the document's own dir must be set for the rtl
  // case to really exercise RTL (tokens.css reads `:root[dir="rtl"]`).
  beforeEach(() => {
    document.documentElement.dir = dir;
  });

  afterEach(() => {
    document.documentElement.dir = "";
  });

  function renderSheet(overrides: Partial<SheetProps> = {}) {
    const onOpenChange = overrides.onOpenChange ?? vi.fn();
    render(
      <div dir={dir}>
        <Sheet
          open
          onOpenChange={onOpenChange}
          title="Lineage"
          closeLabel="Close"
          {...overrides}
        >
          <p>Side panel content</p>
        </Sheet>
      </div>,
    );
    return onOpenChange;
  }

  it("sets the document dir for this case", () => {
    expect(document.documentElement.dir).toBe(dir);
  });

  it("renders its title, description and children while open", () => {
    renderSheet({ description: "Where this row came from." });

    expect(screen.getByRole("heading", { name: "Lineage" })).toBeTruthy();
    expect(screen.getByText("Where this row came from.")).toBeTruthy();
    expect(screen.getByText("Side panel content")).toBeTruthy();
  });

  it("renders nothing when closed", () => {
    renderSheet({ open: false });

    expect(screen.queryByText("Side panel content")).toBeNull();
  });

  it("positions at the inline-end edge and animates in/out via keyframes", () => {
    renderSheet();

    const panel = screen
      .getByText("Side panel content")
      .closest('[class*="end-0"]');
    expect(panel).not.toBeNull();
    expect(panel?.className).toContain(
      "data-[state=open]:animate-[sheet-slide-in_var(--duration-base)_ease-out]",
    );
    expect(panel?.className).toContain(
      "data-[state=closed]:animate-[sheet-slide-out_var(--duration-base)_ease-in]",
    );
  });

  it("has an accessible, >=44px close button that calls onOpenChange(false)", () => {
    const onOpenChange = renderSheet();

    const closeButton = screen.getByRole("button", { name: "Close" });
    expect(closeButton.className).toContain("min-h-11");
    expect(closeButton.className).toContain("min-w-11");

    fireEvent.click(closeButton);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("closes on Escape", () => {
    const onOpenChange = renderSheet();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("has no aria-describedby and logs no warning when no description is given", () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    renderSheet();

    expect(
      screen.getByRole("dialog").getAttribute("aria-describedby"),
    ).toBeNull();
    expect(warnSpy).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });
});
