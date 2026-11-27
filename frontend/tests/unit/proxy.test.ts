// @vitest-environment node
import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";
import proxy, { config } from "../../src/proxy";

function request(
  path: string,
  init?: { cookie?: string; acceptLanguage?: string },
) {
  const headers = new Headers();
  if (init?.cookie) headers.set("cookie", init.cookie);
  if (init?.acceptLanguage) headers.set("accept-language", init.acceptLanguage);
  return new NextRequest(new URL(path, "http://localhost:3000"), { headers });
}

describe("proxy locale negotiation (D10: cookie, then Accept-Language, then en)", () => {
  it("falls back to en with no cookie or Accept-Language", async () => {
    const response = await proxy(request("/"));
    expect(response.headers.get("location")).toBe("http://localhost:3000/en");
  });

  it("honors an Accept-Language: ar request with no cookie", async () => {
    const response = await proxy(request("/", { acceptLanguage: "ar" }));
    expect(response.headers.get("location")).toBe("http://localhost:3000/ar");
  });

  it("prefers the locale cookie over Accept-Language", async () => {
    const response = await proxy(
      request("/", { cookie: "NEXT_LOCALE=en", acceptLanguage: "ar" }),
    );
    expect(response.headers.get("location")).toBe("http://localhost:3000/en");
  });
});

describe("proxy protected-route guard (S-64: UX only)", () => {
  it("redirects a protected path without either cookie to sign-in, with a returnTo", async () => {
    const response = await proxy(request("/en/dashboard?tab=all"));

    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/en/sign-in");
    expect(location.searchParams.get("returnTo")).toBe("/en/dashboard?tab=all");
  });

  it("passes through with the access cookie present", async () => {
    const response = await proxy(
      request("/en/dashboard", { cookie: "replora_access=a" }),
    );
    expect(response.headers.get("location")).toBeNull();
  });

  it("passes through with the refresh cookie present", async () => {
    const response = await proxy(
      request("/en/dashboard", { cookie: "replora_refresh=r" }),
    );
    expect(response.headers.get("location")).toBeNull();
  });

  it.each([
    "sign-in",
    "sign-up",
    "verify-email",
    "mfa",
    "forgot-password",
    "reset-password",
    "privacy",
    "terms",
  ])("lets the public page %s through without cookies", async (page) => {
    const response = await proxy(request(`/en/${page}`));
    expect(response.headers.get("location")).toBeNull();
  });

  it("lets a signed-out request through to /ar/mfa", async () => {
    const response = await proxy(request("/ar/mfa"));
    expect(response.headers.get("location")).toBeNull();
  });

  it("never produces a malicious returnTo for a crafted path", async () => {
    const response = await proxy(request("/en/%0Adashboard"));

    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/en/sign-in");
    expect(location.searchParams.has("returnTo")).toBe(false);
  });

  it("excludes api, _next and static files from the matcher", () => {
    const matcher = new RegExp(`^${config.matcher}$`);
    expect(matcher.test("/en/dashboard")).toBe(true);
    expect(matcher.test("/api/v1/auth/me")).toBe(false);
    expect(matcher.test("/_next/static/chunk.js")).toBe(false);
    expect(matcher.test("/favicon.ico")).toBe(false);
  });
});
