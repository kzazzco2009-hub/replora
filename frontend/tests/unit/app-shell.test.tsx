import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "../../src/components/shell/app-shell";
import { ThemeProvider } from "../../src/components/theme/theme-provider";
import messages from "../../messages/en.json";

vi.mock("next/navigation", () => ({ usePathname: () => "/en" }));
vi.mock("@/i18n/routing", () => ({
  usePathname: () => "/",
  useRouter: () => ({ replace: vi.fn() }),
}));

// next-themes reads this on mount; jsdom has no real media query engine.
window.matchMedia = vi.fn().mockImplementation((query: string) => ({
  matches: false,
  media: query,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  addListener: vi.fn(),
  removeListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));

function renderShell() {
  return render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <ThemeProvider defaultTheme="system">
        <AppShell>
          <p>page content</p>
        </AppShell>
      </ThemeProvider>
    </NextIntlClientProvider>,
  );
}

describe("AppShell", () => {
  it("renders the sidebar, icon rail and bottom tab bar, with Home active for the current path", () => {
    renderShell();
    expect(
      screen.getAllByRole("navigation", { name: "Primary navigation" }),
    ).toHaveLength(3);
    for (const link of screen.getAllByRole("link", { name: "Home" })) {
      expect(link.getAttribute("aria-current")).toBe("page");
    }
  });

  it("renders page content in one <main>, reachable by a skip link", () => {
    renderShell();
    const main = screen.getByRole("main");
    expect(main.textContent).toContain("page content");
    expect(main.getAttribute("id")).toBe("main-content");
    expect(
      screen
        .getByRole("link", { name: "Skip to main content" })
        .getAttribute("href"),
    ).toBe("#main-content");
  });
});
