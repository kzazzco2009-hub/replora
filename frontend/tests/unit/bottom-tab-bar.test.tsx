import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BottomTabBar } from "../../src/components/shell/bottom-tab-bar";
import { NAV_ITEMS } from "../../src/components/shell/nav-items";
import type { ShellNavItem } from "../../src/components/shell/side-nav";

const items: ShellNavItem[] = NAV_ITEMS.map((item) => ({
  id: item.id,
  href: `/en${item.path}`,
  label: item.id,
  icon: item.icon,
  active: false,
}));

function renderBar() {
  render(<BottomTabBar items={items} navLabel="Nav" moreLabel="More" />);
  return screen.getByRole("navigation", { name: "Nav" });
}

describe("BottomTabBar", () => {
  it("is hidden from sm up, and follows design.md order: Home, New run, Runs, Files, then More", () => {
    const nav = renderBar();
    expect(nav.className).toMatch(/\bsm:hidden\b/);
    const order = Array.from(
      nav.querySelectorAll(":scope > a, :scope > details > summary"),
    ).map((el) =>
      el.tagName === "SUMMARY" ? "more" : el.getAttribute("aria-label"),
    );
    expect(order).toEqual(["home", "newRun", "runs", "files", "more"]);
  });

  it("reveals Workflows and Settings behind the More disclosure", () => {
    const nav = renderBar();
    const details = nav.querySelector("details")!;
    expect(details.open).toBe(false);
    fireEvent.click(details.querySelector("summary")!);
    expect(details.open).toBe(true);
    expect(screen.getByRole("link", { name: "workflows" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "settings" })).toBeTruthy();
  });
});
