import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Sheet } from "../../src/components/ui/sheet";

describe.each(["ltr", "rtl"] as const)("Sheet (dir=%s)", (dir) => {
  it("renders its title, description and children while open", () => {
    render(
      <div dir={dir}>
        <Sheet
          open
          onOpenChange={vi.fn()}
          title="Lineage"
          closeLabel="Close"
          description="Where this row came from."
        >
          <p>Side panel content</p>
        </Sheet>
      </div>,
    );

    expect(screen.getByRole("heading", { name: "Lineage" })).toBeTruthy();
    expect(screen.getByText("Where this row came from.")).toBeTruthy();
    expect(screen.getByText("Side panel content")).toBeTruthy();
  });

  it("renders nothing when closed", () => {
    render(
      <div dir={dir}>
        <Sheet
          open={false}
          onOpenChange={vi.fn()}
          title="Lineage"
          closeLabel="Close"
        >
          <p>Side panel content</p>
        </Sheet>
      </div>,
    );

    expect(screen.queryByText("Side panel content")).toBeNull();
  });

  it("positions at the inline-end edge and slides from there, in both directions", () => {
    render(
      <div dir={dir}>
        <Sheet open onOpenChange={vi.fn()} title="Lineage" closeLabel="Close">
          <p>Side panel content</p>
        </Sheet>
      </div>,
    );

    const panel = screen
      .getByText("Side panel content")
      .closest('[class*="end-0"]');
    expect(panel).not.toBeNull();
    expect(panel?.className).toContain(
      "ltr:data-[state=closed]:translate-x-full",
    );
    expect(panel?.className).toContain(
      "rtl:data-[state=closed]:-translate-x-full",
    );
  });

  it("has an accessible, >=44px close button that calls onOpenChange(false)", () => {
    const onOpenChange = vi.fn();
    render(
      <div dir={dir}>
        <Sheet
          open
          onOpenChange={onOpenChange}
          title="Lineage"
          closeLabel="Close"
        >
          <p>Side panel content</p>
        </Sheet>
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
        <Sheet
          open
          onOpenChange={onOpenChange}
          title="Lineage"
          closeLabel="Close"
        >
          <p>Side panel content</p>
        </Sheet>
      </div>,
    );

    fireEvent.keyDown(document, { key: "Escape" });
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
