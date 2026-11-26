import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NAV_ITEMS } from "../../src/components/shell/nav-items";
import { IconRail, Sidebar } from "../../src/components/shell/side-nav";
import type { ShellNavItem } from "../../src/components/shell/side-nav";

const items: ShellNavItem[] = NAV_ITEMS.map((item) => ({
  id: item.id,
  href: `/en${item.path}`,
  label: item.id,
  icon: item.icon,
  active: false,
}));

const ORDER = ["home", "newRun", "runs", "workflows", "files", "settings"];

describe("Sidebar", () => {
  it("is hidden below lg, shown as a flex column from lg up, with all 6 items in design order", () => {
    render(<Sidebar items={items} navLabel="Nav" />);
    const nav = screen.getByRole("navigation", { name: "Nav" });
    expect(nav.className).toMatch(/\bhidden\b/);
    expect(nav.className).toMatch(/\blg:flex\b/);
    const links = screen.getAllByRole("link").map((link) => link.textContent);
    expect(links).toEqual(ORDER);
  });
});

describe("IconRail", () => {
  it("is hidden outside sm..lg, and renders all 6 items icon-only with an accessible name", () => {
    render(<IconRail items={items} navLabel="Nav" />);
    const nav = screen.getByRole("navigation", { name: "Nav" });
    expect(nav.className).toMatch(/\bhidden\b/);
    expect(nav.className).toMatch(/\bsm:flex\b/);
    expect(nav.className).toMatch(/\blg:hidden\b/);
    const links = screen.getAllByRole("link");
    expect(links.map((link) => link.getAttribute("aria-label"))).toEqual(ORDER);
    expect(links[0].querySelector("span")?.className).toMatch(/\bsr-only\b/);
  });
});
