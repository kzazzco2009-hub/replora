// @vitest-environment node
import { renderToString } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { THEME_COOKIE } from "../../src/lib/theme-cookie";

let themeCookie: string | undefined;

vi.mock("next/headers", () => ({
  cookies: async () => ({
    get: (name: string) =>
      name === THEME_COOKIE && themeCookie !== undefined
        ? { value: themeCookie }
        : undefined,
  }),
}));

// next-intl/server's `react-server` build isn't resolvable outside Next's
// own RSC bundler (see next-intl's testing docs); its locale cache side
// effect isn't under test here, so it's mocked out as a no-op.
vi.mock("next-intl/server", () => ({
  setRequestLocale: () => {},
}));

// Next's RSC renderer supplies the locale to this provider automatically.
vi.mock("next-intl", async (importOriginal) => ({
  ...(await importOriginal<typeof import("next-intl")>()),
  NextIntlClientProvider: ({ children }: { children: React.ReactNode }) =>
    children,
}));

vi.mock("@/components/shell/app-shell", () => ({
  AppShell: () => null,
}));

const LocaleLayout = (await import("../../src/app/[locale]/layout")).default;

describe.each([
  { locale: "en", dir: "ltr" },
  { locale: "ar", dir: "rtl" },
])("LocaleLayout server markup (dir=$dir)", ({ locale, dir }) => {
  async function renderRoot(cookie: string | undefined) {
    themeCookie = cookie;
    const element = await LocaleLayout({
      children: null,
      params: Promise.resolve({ locale }),
    });
    const html = renderToString(element);
    const root = html.match(/<html\b[^>]*>/)?.[0];
    if (!root) throw new Error("Expected a server-rendered <html> element");
    return root;
  }

  it("serves the locale and direction on the document root", async () => {
    const root = await renderRoot(undefined);
    expect(root).toContain(`lang="${locale}"`);
    expect(root).toContain(`dir="${dir}"`);
  });

  it.each(["light", "dark"])(
    "serves the explicit %s theme before hydration",
    async (theme) => {
      expect(await renderRoot(theme)).toContain(`data-theme="${theme}"`);
    },
  );

  it.each([undefined, "system"])(
    "leaves the system preference to CSS for cookie %s",
    async (cookie) => {
      expect(await renderRoot(cookie)).not.toContain("data-theme=");
    },
  );
});
