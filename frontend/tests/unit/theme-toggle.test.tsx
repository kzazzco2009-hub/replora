import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ThemeCookieSync } from "../../src/components/theme/theme-cookie-sync";
import { ThemeProvider } from "../../src/components/theme/theme-provider";
import { ThemeToggle } from "../../src/components/theme/theme-toggle";
import messages from "../../messages/en.json";
import ar from "../../messages/ar.json";
import { THEME_COOKIE } from "../../src/lib/theme-cookie";

function mockSystemTheme(prefersDark: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: query === "(prefers-color-scheme: dark)" && prefersDark,
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

function clearThemeCookie() {
  document.cookie = "theme=; path=/; max-age=0";
}

beforeEach(() => {
  mockSystemTheme(false);
  localStorage.clear();
  clearThemeCookie();
  document.documentElement.removeAttribute("data-theme");
});

afterEach(() => {
  localStorage.clear();
  clearThemeCookie();
  document.documentElement.removeAttribute("data-theme");
});

describe("ThemeToggle", () => {
  it("sets data-theme on the html element when a theme is picked", () => {
    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <ThemeProvider defaultTheme="system">
          <ThemeToggle />
        </ThemeProvider>
      </NextIntlClientProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Dark" }));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");

    fireEvent.click(screen.getByRole("button", { name: "Light" }));
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("with no cookie and a dark system preference, resolves to dark before any user action", () => {
    mockSystemTheme(true);

    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <ThemeProvider defaultTheme="system">
          <ThemeCookieSync />
          <ThemeToggle />
        </ThemeProvider>
      </NextIntlClientProvider>,
    );

    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    // "system" is never cached as a cookie (see theme-cookie-sync.tsx):
    // a stale cookie could disagree with a future OS preference change.
    expect(document.cookie).not.toMatch(/theme=(light|dark)/);
  });
});

describe.each([
  { locale: "en", dir: "ltr", messages },
  { locale: "ar", dir: "rtl", messages: ar },
] as const)("ThemeToggle (dir=$dir)", ({ locale, dir, messages }) => {
  const labels = messages.theme.toggle;

  function renderToggle() {
    return render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <ThemeProvider defaultTheme="system">
            <ThemeCookieSync />
            <ThemeToggle />
          </ThemeProvider>
        </NextIntlClientProvider>
      </div>,
    );
  }

  function expectTheme(theme: "light" | "dark") {
    expect(document.documentElement.getAttribute("data-theme")).toBe(theme);
  }

  it.each([
    { theme: "dark", prefersDark: false },
    { theme: "light", prefersDark: true },
  ] as const)(
    "restores the explicit $theme choice on remount",
    ({ theme, prefersDark }) => {
      mockSystemTheme(prefersDark);
      const { unmount } = renderToggle();

      fireEvent.click(screen.getByRole("button", { name: labels[theme] }));
      expectTheme(theme);
      expect(document.cookie.split("; ")).toContain(`${THEME_COOKIE}=${theme}`);

      unmount();
      document.documentElement.removeAttribute("data-theme");
      renderToggle();

      expectTheme(theme);
      expect(
        screen.getByRole("button", { name: labels[theme], pressed: true }),
      ).toBeTruthy();
    },
  );

  it.each([
    { theme: "dark", prefersDark: true },
    { theme: "light", prefersDark: false },
  ] as const)(
    "uses the system's $theme preference on first visit",
    ({ theme, prefersDark }) => {
      mockSystemTheme(prefersDark);
      renderToggle();

      expectTheme(theme);
      expect(document.cookie).not.toContain(`${THEME_COOKIE}=`);
    },
  );

  it("clears the explicit choice and resumes following the system", () => {
    mockSystemTheme(true);
    renderToggle();

    fireEvent.click(screen.getByRole("button", { name: labels.light }));
    expectTheme("light");

    fireEvent.click(screen.getByRole("button", { name: labels.system }));
    expectTheme("dark");
    expect(document.cookie).not.toContain(`${THEME_COOKIE}=`);
  });
});
