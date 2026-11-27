import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import AppLayout from "../../src/app/[locale]/(app)/layout";
import { ThemeProvider } from "../../src/components/theme/theme-provider";
import messages from "../../messages/en.json";

vi.mock("next/navigation", () => ({
  usePathname: () => "/en",
  useRouter: () => ({ replace: vi.fn() }),
  useParams: () => ({ locale: "en" }),
}));
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
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <QueryClientProvider client={client}>
          <ThemeProvider defaultTheme="system">
            <AppLayout>
              <p>page content</p>
            </AppLayout>
          </ThemeProvider>
        </QueryClientProvider>
      </NextIntlClientProvider>,
    );

    expect(screen.getByText("page content")).toBeTruthy();
    expect(screen.getByRole("main").getAttribute("id")).toBe("main-content");
  });
});
