"use client";

import { useTheme } from "next-themes";
import { useEffect } from "react";
import { clearThemeCookie, serializeThemeCookie } from "@/lib/theme-cookie";

/**
 * Mirrors an explicit light/dark choice into a cookie so the next server
 * render already has the right `data-theme` (see layout.tsx). "system" is
 * never cached: a stale cookie could disagree with the OS preference by the
 * next visit, so "system" clears the cookie and lets the CSS media-query
 * fallback in tokens.css resolve it fresh on every load instead.
 */
export function ThemeCookieSync() {
  const { theme } = useTheme();

  useEffect(() => {
    if (theme === "light" || theme === "dark") {
      document.cookie = serializeThemeCookie(theme);
    } else if (theme === "system") {
      document.cookie = clearThemeCookie();
    }
  }, [theme]);

  return null;
}
