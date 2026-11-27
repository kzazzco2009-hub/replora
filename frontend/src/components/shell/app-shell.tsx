"use client";

import { usePathname } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { LocaleSwitch } from "@/components/locale/locale-switch";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { BottomTabBar } from "./bottom-tab-bar";
import { NAV_ITEMS } from "./nav-items";
import { IconRail, Sidebar, type ShellNavItem } from "./side-nav";
import { UserMenu } from "./user-menu";

export function AppShell({ children }: { children: ReactNode }) {
  const locale = useLocale();
  const pathname = usePathname();
  const t = useTranslations("nav");
  const shellT = useTranslations("shell");
  const navLabel = shellT("primaryNav");

  const items: ShellNavItem[] = NAV_ITEMS.map((item) => {
    const href = `/${locale}${item.path}`;
    return {
      id: item.id,
      href,
      label: t(item.id),
      icon: item.icon,
      active: pathname === href,
    };
  });

  return (
    <div className="flex min-h-dvh flex-col lg:flex-row">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:start-4 focus:top-4 focus:z-50 focus:rounded-control focus:bg-surface focus:px-4 focus:py-2"
      >
        {shellT("skipToContent")}
      </a>
      <Sidebar items={items} navLabel={navLabel} />
      <IconRail items={items} navLabel={navLabel} />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-end gap-2 border-b border-line p-2">
          <LocaleSwitch />
          <ThemeToggle />
          <UserMenu />
        </header>
        <main id="main-content" className="flex-1 p-4 pb-20 sm:pb-4">
          {children}
        </main>
      </div>
      <BottomTabBar items={items} navLabel={navLabel} moreLabel={t("more")} />
    </div>
  );
}
