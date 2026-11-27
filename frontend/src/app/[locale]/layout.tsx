import type { Metadata } from "next";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { Readex_Pro } from "next/font/google";
import { notFound } from "next/navigation";
import { cookies } from "next/headers";
import "../globals.css";
import { QueryProvider } from "@/components/providers/query-provider";
import { ThemeCookieSync } from "@/components/theme/theme-cookie-sync";
import { ThemeProvider } from "@/components/theme/theme-provider";
import { parseThemeCookie, THEME_COOKIE } from "@/lib/theme-cookie";
import { localeDirection, routing } from "@/i18n/routing";

export const metadata: Metadata = {
  title: "Replora",
  description: "Replora",
};

// design.md §3: one family for AR and EN together, self-hosted at build
// time by next/font (no runtime request to Google, no font files to commit).
const readexPro = Readex_Pro({
  subsets: ["arabic", "latin"],
  variable: "--font-readex-pro",
});

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}>) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }
  setRequestLocale(locale);

  const cookieStore = await cookies();
  const initialTheme = parseThemeCookie(cookieStore.get(THEME_COOKIE)?.value);

  // `data-theme` is set here only for an explicit light/dark cookie. With no
  // cookie ("system", or never visited before), the attribute is omitted on
  // purpose: tokens.css then resolves colors from `prefers-color-scheme`,
  // which is always live and never stale, so there is no flash to cache for.
  return (
    <html
      lang={locale}
      dir={localeDirection(locale)}
      data-theme={initialTheme}
      className={readexPro.variable}
      suppressHydrationWarning
    >
      <body>
        <NextIntlClientProvider>
          <QueryProvider>
            <ThemeProvider defaultTheme="system">
              <ThemeCookieSync />
              {children}
            </ThemeProvider>
          </QueryProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
