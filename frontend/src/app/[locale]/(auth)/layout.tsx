"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { LocaleSwitch } from "@/components/locale/locale-switch";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Link } from "@/i18n/routing";

/** Centered card shell for sign-in, sign-up and the other pre-login screens (design.md §5). */
export default function AuthLayout({ children }: { children: ReactNode }) {
  const shellT = useTranslations("shell");
  const homeT = useTranslations("home");

  return (
    <div className="flex min-h-dvh flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:start-4 focus:top-4 focus:z-50 focus:rounded-control focus:bg-surface focus:px-4 focus:py-2"
      >
        {shellT("skipToContent")}
      </a>
      <header className="flex items-center justify-between gap-2 p-4">
        <Link href="/" className="text-lg font-semibold text-ink">
          {homeT("title")}
        </Link>
        <div className="flex items-center gap-2">
          <LocaleSwitch />
          <ThemeToggle />
        </div>
      </header>
      <main
        id="main-content"
        className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-8"
      >
        {children}
      </main>
    </div>
  );
}
