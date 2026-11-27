import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ComponentProps } from "react";
import { describe, expect, it, vi } from "vitest";
import AuthLayout from "../../src/app/[locale]/(auth)/layout";
import { ThemeProvider } from "../../src/components/theme/theme-provider";
import messages from "../../messages/en.json";

vi.mock("@/i18n/routing", () => ({
  usePathname: () => "/",
  useRouter: () => ({ replace: vi.fn() }),
  Link: ({ href, ...props }: ComponentProps<"a">) => (
    <a href={href} {...props} />
  ),
}));

window.matchMedia = vi.fn().mockImplementation((query: string) => ({
  matches: false,
  media: query,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  addListener: vi.fn(),
  removeListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));

function renderLayout(dir: "ltr" | "rtl") {
  return render(
    <div dir={dir}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <ThemeProvider defaultTheme="system">
          <AuthLayout>
            <p>form content</p>
          </AuthLayout>
        </ThemeProvider>
      </NextIntlClientProvider>
    </div>,
  );
}

describe.each(["ltr", "rtl"] as const)("AuthLayout (dir=%s)", (dir) => {
  it("renders a skip link and the main landmark around the children", () => {
    renderLayout(dir);

    const main = screen.getByRole("main");
    expect(main.getAttribute("id")).toBe("main-content");
    expect(main.textContent).toContain("form content");
    expect(
      screen
        .getByRole("link", { name: "Skip to main content" })
        .getAttribute("href"),
    ).toBe("#main-content");
  });

  it("renders the Replora name as a link, plus the locale and theme switches", () => {
    renderLayout(dir);

    expect(screen.getByRole("link", { name: "Replora" })).toBeTruthy();
    expect(screen.getByRole("group", { name: "Language" })).toBeTruthy();
    expect(screen.getByRole("group", { name: "Theme" })).toBeTruthy();
  });
});
