import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import AppLayout from "../../src/app/[locale]/(app)/layout";
import { ThemeProvider } from "../../src/components/theme/theme-provider";
import messages from "../../messages/en.json";

vi.mock("next/navigation", () => ({ usePathname: () => "/en" }));
vi.mock("@/i18n/routing", () => ({
  usePathname: () => "/",
  useRouter: () => ({ replace: vi.fn() }),
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

describe("AppLayout", () => {
  it("wraps its children in the app shell", () => {
    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <ThemeProvider defaultTheme="system">
          <AppLayout>
            <p>page content</p>
          </AppLayout>
        </ThemeProvider>
      </NextIntlClientProvider>,
    );

    expect(screen.getByText("page content")).toBeTruthy();
    expect(screen.getByRole("main").getAttribute("id")).toBe("main-content");
  });
});
