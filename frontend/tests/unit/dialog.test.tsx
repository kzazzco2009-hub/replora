import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Dialog, type DialogProps } from "../../src/components/ui/dialog";

describe.each(["ltr", "rtl"] as const)("Dialog (dir=%s)", (dir) => {
  // RadixDialog.Portal renders into document.body, outside the <div dir>
  // wrapper below, so the document's own dir must be set for the rtl
  // case to really exercise RTL.
  beforeEach(() => {
    document.documentElement.dir = dir;
  });

  afterEach(() => {
    document.documentElement.dir = "";
  });

  function renderDialog(overrides: Partial<DialogProps> = {}) {
    const onOpenChange = overrides.onOpenChange ?? vi.fn();
    render(
      <div dir={dir}>
        <Dialog
          open
          onOpenChange={onOpenChange}
          title="Delete workspace"
          closeLabel="Close"
          {...overrides}
        >
          <p>Body content</p>
        </Dialog>
      </div>,
    );
    return onOpenChange;
  }

  it("sets the document dir for this case", () => {
    expect(document.documentElement.dir).toBe(dir);
  });

  it("renders its title, description and children while open", () => {
    renderDialog({ description: "This cannot be undone." });

    expect(
      screen.getByRole("heading", { name: "Delete workspace" }),
    ).toBeTruthy();
    expect(screen.getByText("This cannot be undone.")).toBeTruthy();
    expect(screen.getByText("Body content")).toBeTruthy();
  });

  it("renders nothing when closed", () => {
    renderDialog({ open: false });

    expect(screen.queryByText("Body content")).toBeNull();
  });

  it("has an accessible, >=44px close button that calls onOpenChange(false)", () => {
    const onOpenChange = renderDialog();

    const closeButton = screen.getByRole("button", { name: "Close" });
    expect(closeButton.className).toContain("min-h-11");
    expect(closeButton.className).toContain("min-w-11");

    fireEvent.click(closeButton);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("closes on Escape", () => {
    const onOpenChange = renderDialog();

    fireEvent.keyDown(document, { key: "Escape" });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("has no aria-describedby and logs no warning when no description is given", () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
    renderDialog();

    expect(
      screen.getByRole("dialog").getAttribute("aria-describedby"),
    ).toBeNull();
    expect(warnSpy).not.toHaveBeenCalled();
    warnSpy.mockRestore();
  });
});
