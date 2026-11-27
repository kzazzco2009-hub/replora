import { readFile } from "node:fs/promises";
import { join } from "node:path";
import tailwind from "@tailwindcss/postcss";
import postcss, { type Root } from "postcss";
import ar from "../../messages/ar.json";
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeAll, describe, expect, it, vi } from "vitest";
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

describe("AppShell responsive CSS", () => {
  let css: Root;

  beforeAll(async () => {
    const base = join(import.meta.dirname, "../../src");
    const from = join(base, "app/globals.css");
    const input = await readFile(from, "utf8");
    const result = await postcss([
      tailwind({ base, optimize: { minify: false } }),
    ]).process(input, { from });
    css = result.root;
  });

  function displayAtWidth(nav: HTMLElement, width: number) {
    // Only the shell's single-class display rules in the compiled stylesheet
    // are evaluated here. The default initial font size is 16 CSS px.
    let display = "block";
    css.walkDecls("display", (declaration) => {
      const rule = declaration.parent;
      if (rule?.type !== "rule" || !rule.selector.startsWith(".")) return;
      const className = rule.selector.slice(1).replaceAll("\\:", ":");
      if (!nav.classList.contains(className)) return;

      const parent = rule.parent;
      if (parent?.type === "atrule" && parent.name === "media") {
        const breakpoint = /^\((?:min-width:\s*|width >= )([\d.]+)rem\)$/.exec(
          parent.params,
        )?.[1];
        expect(breakpoint, parent.params).toBeDefined();
        if (width < Number(breakpoint) * 16) return;
      }
      display = declaration.value;
    });
    return display;
  }

  describe.each([
    { locale: "en", dir: "ltr", messages },
    { locale: "ar", dir: "rtl", messages: ar },
  ] as const)("dir=$dir", ({ locale, messages }) => {
    it.each([
      { width: 1440, sidebar: "flex", rail: "none", tabs: "none" },
      { width: 820, sidebar: "none", rail: "flex", tabs: "none" },
      { width: 390, sidebar: "none", rail: "none", tabs: "flex" },
    ])(
      "selects the expected navigation at $width px",
      ({ width, sidebar, rail, tabs }) => {
        const { container } = render(
          <div dir={locale === "en" ? "ltr" : "rtl"}>
            <NextIntlClientProvider locale={locale} messages={messages}>
              <ThemeProvider defaultTheme="system">
                <AppShell>
                  <p>page content</p>
                </AppShell>
              </ThemeProvider>
            </NextIntlClientProvider>
          </div>,
        );
        const navs = container.querySelectorAll<HTMLElement>("nav");
        expect(navs).toHaveLength(3);
        expect(
          Array.from(navs, (nav) => nav.getAttribute("aria-label")),
        ).toEqual(Array(3).fill(messages.shell.primaryNav));
        expect(Array.from(navs, (nav) => displayAtWidth(nav, width))).toEqual([
          sidebar,
          rail,
          tabs,
        ]);
      },
    );
  });
});
