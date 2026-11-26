import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Dialog } from "../../src/components/ui/dialog";

describe.each(["ltr", "rtl"] as const)("Dialog (dir=%s)", (dir) => {
  it("renders its title, description and children while open", () => {
    render(
      <div dir={dir}>
        <Dialog
          open
          onOpenChange={vi.fn()}
          title="Delete workspace"
          closeLabel="Close"
          description="This cannot be undone."
        >
          <p>Body content</p>
        </Dialog>
      </div>,
    );

    expect(
      screen.getByRole("heading", { name: "Delete workspace" }),
    ).toBeTruthy();
    expect(screen.getByText("This cannot be undone.")).toBeTruthy();
    expect(screen.getByText("Body content")).toBeTruthy();
  });

  it("renders nothing when closed", () => {
    render(
      <div dir={dir}>
        <Dialog
          open={false}
          onOpenChange={vi.fn()}
          title="Delete workspace"
          closeLabel="Close"
        >
          <p>Body content</p>
        </Dialog>
      </div>,
    );

    expect(screen.queryByText("Body content")).toBeNull();
  });

  it("has an accessible, >=44px close button that calls onOpenChange(false)", () => {
    const onOpenChange = vi.fn();
    render(
      <div dir={dir}>
        <Dialog
          open
          onOpenChange={onOpenChange}
          title="Delete workspace"
          closeLabel="Close"
        >
          <p>Body content</p>
        </Dialog>
      </div>,
    );

    const closeButton = screen.getByRole("button", { name: "Close" });
    expect(closeButton.className).toContain("min-h-11");
    expect(closeButton.className).toContain("min-w-11");

    fireEvent.click(closeButton);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("closes on Escape", () => {
    const onOpenChange = vi.fn();
    render(
      <div dir={dir}>
        <Dialog
          open
          onOpenChange={onOpenChange}
          title="Delete workspace"
          closeLabel="Close"
        >
          <p>Body content</p>
        </Dialog>
      </div>,
    );

    fireEvent.keyDown(document, { key: "Escape" });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
