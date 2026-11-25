// @vitest-environment node
import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";
import proxy from "../../src/proxy";

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
