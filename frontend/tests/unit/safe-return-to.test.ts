import { describe, expect, it } from "vitest";
import { safeReturnTo } from "../../src/lib/safe-return-to";

describe("safeReturnTo", () => {
  it("accepts a same-locale path", () => {
    expect(safeReturnTo("/en/dashboard", "en")).toBe("/en/dashboard");
  });

  it("accepts the locale root, with or without a trailing slash", () => {
    expect(safeReturnTo("/en", "en")).toBe("/en");
    expect(safeReturnTo("/en/", "en")).toBe("/en/");
  });

  it("accepts a path with a query string", () => {
    expect(safeReturnTo("/en/runs?tab=all", "en")).toBe("/en/runs?tab=all");
  });

  it("rejects a path for a different locale", () => {
    expect(safeReturnTo("/ar/dashboard", "en")).toBeNull();
  });

  it("rejects a path back into an auth page", () => {
    expect(safeReturnTo("/en/sign-in", "en")).toBeNull();
    expect(safeReturnTo("/en/sign-up/confirm", "en")).toBeNull();
    expect(safeReturnTo("/en/verify-email", "en")).toBeNull();
    expect(safeReturnTo("/en/forgot-password", "en")).toBeNull();
    expect(safeReturnTo("/en/reset-password", "en")).toBeNull();
  });

  it.each([
    ["not a string", 123],
    ["null", null],
    ["undefined", undefined],
    ["an absolute URL", "https://evil.com"],
    ["protocol-relative", "//evil.com"],
    ["a backslash host trick", "/\\evil.com"],
    ["a bare scheme", "javascript:"],
    ["an encoded slash with no leading slash", "%2f%2f"],
    ["an encoded protocol-relative bypass", "/%2f%2fevil.com"],
    ["an encoded newline", "/en/%0Adashboard"],
    ["empty", ""],
    ["very long", `/en/${"a".repeat(3000)}`],
    ["a stray backslash", "/en/dash\\board"],
    ["a stray @", "/en/da@shboard"],
  ])("rejects %s", (_label, value) => {
    expect(safeReturnTo(value, "en")).toBeNull();
  });
});
