"use client";

import { useTranslations } from "next-intl";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

const OPTIONS = ["light", "dark", "system"] as const;

function noopSubscribe() {
  return () => {};
}

/** False on the server and on the client's first render, true after mount. */
function useMounted(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  );
}

export function ThemeToggle() {
  const t = useTranslations("theme.toggle");
  const { theme, setTheme } = useTheme();
  // `theme` is unknown on the server and on the client's first render
  // (next-themes avoids guessing to prevent a hydration mismatch), so no
  // option is marked pressed until after mount.
  const mounted = useMounted();

  return (
    <div role="group" aria-label={t("groupLabel")}>
      {OPTIONS.map((option) => (
        <button
          key={option}
          type="button"
          aria-pressed={mounted && theme === option}
          onClick={() => setTheme(option)}
        >
          {t(option)}
        </button>
      ))}
    </div>
  );
}
