import type { Metadata } from "next";
import { cookies } from "next/headers";
import "./globals.css";
import { ThemeCookieSync } from "@/components/theme/theme-cookie-sync";
import { ThemeProvider } from "@/components/theme/theme-provider";
import { parseThemeCookie, THEME_COOKIE } from "@/lib/theme-cookie";

export const metadata: Metadata = {
  title: "Replora",
  description: "Replora",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = await cookies();
  const initialTheme = parseThemeCookie(cookieStore.get(THEME_COOKIE)?.value);

  // `data-theme` is set here only for an explicit light/dark cookie. With no
  // cookie ("system", or never visited before), the attribute is omitted on
  // purpose: tokens.css then resolves colors from `prefers-color-scheme`,
  // which is always live and never stale, so there is no flash to cache for.
  return (
    <html lang="en" data-theme={initialTheme} suppressHydrationWarning>
      <body>
        <ThemeProvider defaultTheme="system">
          <ThemeCookieSync />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
