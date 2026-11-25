import { describe, expect, it } from "vitest";
import {
  clearThemeCookie,
  parseThemeCookie,
  serializeThemeCookie,
  THEME_COOKIE,
} from "../../src/lib/theme-cookie";

describe("theme-cookie", () => {
  it("parses light and dark, and nothing else", () => {
    expect(parseThemeCookie("light")).toBe("light");
    expect(parseThemeCookie("dark")).toBe("dark");
    expect(parseThemeCookie("system")).toBeUndefined();
    expect(parseThemeCookie(undefined)).toBeUndefined();
  });

  it("serializes a persistent, lax same-site cookie", () => {
    expect(serializeThemeCookie("dark")).toBe(
      `${THEME_COOKIE}=dark; path=/; max-age=31536000; samesite=lax`,
    );
  });

  it("clears the cookie with an immediately expired max-age", () => {
    expect(clearThemeCookie()).toBe(
      `${THEME_COOKIE}=; path=/; max-age=0; samesite=lax`,
    );
  });
});
