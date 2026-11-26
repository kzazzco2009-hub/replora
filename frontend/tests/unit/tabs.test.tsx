import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Tabs, type TabsProps } from "../../src/components/ui/tabs";

const BASE_TABS = [
  { value: "all", label: "All", content: <p>All rows</p> },
  { value: "different", label: "Different", content: <p>Different rows</p> },
  { value: "missing", label: "Missing", content: <p>Missing rows</p> },
];

describe.each(["ltr", "rtl"] as const)("Tabs (dir=%s)", (dir) => {
  // Tabs has no portal, so `dir` on the component is what actually drives
  // Radix's keyboard-direction logic. document.documentElement.dir is set
  // anyway to match the pattern used by the other components' tests.
  document.documentElement.dir = dir;

  function renderTabs(overrides: Partial<TabsProps> = {}) {
    const onValueChange = overrides.onValueChange ?? vi.fn();
    render(
      <div dir={dir}>
        <Tabs
          label="Results filter"
          tabs={BASE_TABS}
          dir={dir}
          onValueChange={onValueChange}
          {...overrides}
        />
      </div>,
    );
    return onValueChange;
  }

  it("has its aria-label on the tab list", () => {
    renderTabs();

    expect(
      screen.getByRole("tablist", { name: "Results filter" }),
    ).toBeTruthy();
  });

  it("defaults to the first tab when uncontrolled", () => {
    renderTabs();

    expect(
      screen.getByRole("tab", { name: "All" }).getAttribute("aria-selected"),
    ).toBe("true");
    expect(screen.getByText("All rows")).toBeTruthy();
  });

  it("respects defaultValue", () => {
    renderTabs({ defaultValue: "missing" });

    expect(
      screen
        .getByRole("tab", { name: "Missing" })
        .getAttribute("aria-selected"),
    ).toBe("true");
    expect(screen.getByText("Missing rows")).toBeTruthy();
  });

  it("calls onValueChange when a tab is clicked (controlled use)", () => {
    const onValueChange = renderTabs({ value: "all" });

    // Radix's TabsTrigger activates on mousedown, not click; fireEvent.click
    // alone never dispatches a mousedown.
    fireEvent.mouseDown(screen.getByRole("tab", { name: "Different" }));

    expect(onValueChange).toHaveBeenCalledWith("different");
  });

  it("has a >=44px tab trigger", () => {
    renderTabs();

    expect(screen.getByRole("tab", { name: "All" }).className).toContain(
      "min-h-11",
    );
  });

  it("marks the active tab with a border and heavier weight, not colour alone", () => {
    renderTabs();

    const active = screen.getByRole("tab", { name: "All" });
    expect(active.getAttribute("data-state")).toBe("active");
    expect(active.className).toContain("data-[state=active]:border-petrol");
    expect(active.className).toContain("data-[state=active]:font-semibold");

    const inactive = screen.getByRole("tab", { name: "Different" });
    expect(inactive.getAttribute("data-state")).toBe("inactive");
  });

  it("gives roving tabIndex: only the current tab stop is 0, the rest are -1", () => {
    renderTabs();

    // Before any interaction the roving group itself is the sole tab stop
    // (ARIA roving-tabindex pattern); mousedown on a tab is what makes it
    // the current stop, same path a real click takes.
    fireEvent.mouseDown(screen.getByRole("tab", { name: "All" }));

    expect(
      screen.getByRole("tab", { name: "All" }).getAttribute("tabindex"),
    ).toBe("0");
    expect(
      screen.getByRole("tab", { name: "Different" }).getAttribute("tabindex"),
    ).toBe("-1");
    expect(
      screen.getByRole("tab", { name: "Missing" }).getAttribute("tabindex"),
    ).toBe("-1");
  });

  it("moves focus forward and back with the arrow keys, reversed in RTL", async () => {
    renderTabs();

    const all = screen.getByRole("tab", { name: "All" });
    const different = screen.getByRole("tab", { name: "Different" });
    all.focus();

    const forwardKey = dir === "rtl" ? "ArrowLeft" : "ArrowRight";
    fireEvent.keyDown(all, { key: forwardKey });
    // Radix moves focus inside a setTimeout(0), not synchronously.
    await vi.waitFor(() => expect(document.activeElement).toBe(different));

    const backKey = dir === "rtl" ? "ArrowRight" : "ArrowLeft";
    fireEvent.keyDown(different, { key: backKey });
    await vi.waitFor(() => expect(document.activeElement).toBe(all));
  });

  it("moves focus to the first/last tab with Home/End", async () => {
    renderTabs();

    const all = screen.getByRole("tab", { name: "All" });
    const missing = screen.getByRole("tab", { name: "Missing" });
    all.focus();

    fireEvent.keyDown(all, { key: "End" });
    await vi.waitFor(() => expect(document.activeElement).toBe(missing));

    fireEvent.keyDown(missing, { key: "Home" });
    await vi.waitFor(() => expect(document.activeElement).toBe(all));
  });

  it("skips a disabled tab when navigating with arrow keys", async () => {
    renderTabs({
      tabs: [BASE_TABS[0], { ...BASE_TABS[1], disabled: true }, BASE_TABS[2]],
    });

    const all = screen.getByRole("tab", { name: "All" });
    const missing = screen.getByRole("tab", { name: "Missing" });
    all.focus();

    const forwardKey = dir === "rtl" ? "ArrowLeft" : "ArrowRight";
    fireEvent.keyDown(all, { key: forwardKey });
    await vi.waitFor(() => expect(document.activeElement).toBe(missing));
  });
});
