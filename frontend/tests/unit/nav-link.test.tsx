import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NavLink } from "../../src/components/shell/nav-link";
import { NAV_ITEMS } from "../../src/components/shell/nav-items";

const HomeIcon = NAV_ITEMS[0].icon;

describe("NavLink", () => {
  it("renders a link with the label as its accessible name, even icon-only", () => {
    render(
      <NavLink
        href="/en"
        label="Home"
        icon={HomeIcon}
        active={false}
        iconOnly
      />,
    );
    expect(
      screen.getByRole("link", { name: "Home" }).getAttribute("href"),
    ).toBe("/en");
  });

  it("sets aria-current only when active", () => {
    const { rerender } = render(
      <NavLink href="/en" label="Home" icon={HomeIcon} active />,
    );
    expect(screen.getByRole("link").getAttribute("aria-current")).toBe("page");
    rerender(
      <NavLink href="/en" label="Home" icon={HomeIcon} active={false} />,
    );
    expect(screen.getByRole("link").getAttribute("aria-current")).toBeNull();
  });
});
