// @vitest-environment node
import { describe, expect, it, vi } from "vitest";
import { THEME_COOKIE } from "../../src/lib/theme-cookie";

vi.mock("next/headers", () => ({
  cookies: async () => ({
    get: (name: string) =>
      name === THEME_COOKIE ? { value: "dark" } : undefined,
  }),
}));

// next-intl/server's `react-server` build isn't resolvable outside Next's
// own RSC bundler (see next-intl's testing docs); its locale cache side
// effect isn't under test here, so it's mocked out as a no-op.
vi.mock("next-intl/server", () => ({
  setRequestLocale: () => {},
}));

const LocaleLayout = (await import("../../src/app/[locale]/layout")).default;

describe("LocaleLayout", () => {
  it("sets html lang and dir from the locale param", async () => {
    const element = await LocaleLayout({
      children: null,
      params: Promise.resolve({ locale: "en" }),
    });
    expect(element.props.lang).toBe("en");
    expect(element.props.dir).toBe("ltr");
  });

  it("mirrors the Arabic locale to rtl", async () => {
    const element = await LocaleLayout({
      children: null,
      params: Promise.resolve({ locale: "ar" }),
    });
    expect(element.props.lang).toBe("ar");
    expect(element.props.dir).toBe("rtl");
  });

  it("still reads the theme cookie for the no-flash data-theme attribute (#29)", async () => {
    const element = await LocaleLayout({
      children: null,
      params: Promise.resolve({ locale: "en" }),
    });
    expect(element.props["data-theme"]).toBe("dark");
  });
});
