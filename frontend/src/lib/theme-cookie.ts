export const THEME_COOKIE = "theme";

export type ResolvedTheme = "light" | "dark";

export function parseThemeCookie(
  value: string | undefined,
): ResolvedTheme | undefined {
  return value === "light" || value === "dark" ? value : undefined;
}

export function serializeThemeCookie(theme: ResolvedTheme): string {
  return `${THEME_COOKIE}=${theme}; path=/; max-age=31536000; samesite=lax`;
}

export function clearThemeCookie(): string {
  return `${THEME_COOKIE}=; path=/; max-age=0; samesite=lax`;
}
