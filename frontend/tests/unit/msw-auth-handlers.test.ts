import { describe, expect, it } from "vitest";
import { setScenario } from "../msw/scenarios";

// Relative URLs: msw resolves a relative handler path against `location`
// (jsdom's default origin in tests), so a relative fetch here is what
// actually lines up with it — an absolute "http://localhost" URL would
// use a different, non-matching origin and silently miss every handler.
const loginRequest = () =>
  fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: "salma@example.com", password: "x" }),
  });

describe("MSW auth handlers (scenario switching)", () => {
  it("answers the default ok scenario when none is set", async () => {
    const res = await fetch("/api/v1/auth/csrf");
    expect(res.status).toBe(204);
  });

  it("serves a 204/null-body case without a JSON-parse error", async () => {
    const res = await fetch("/api/v1/auth/logout", {
      method: "POST",
    });
    expect(res.status).toBe(204);
    expect(await res.text()).toBe("");
  });

  it("switches an endpoint to a named scenario", async () => {
    setScenario("auth_login", "mfa_required");

    const res = await loginRequest();

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ mfa_required: true });
  });

  it("falls back to ok for the next test, since setup.ts resets scenarios", async () => {
    const res = await loginRequest();

    expect(res.status).toBe(200);
    const body = (await res.json()) as { mfa_required?: boolean };
    expect(body.mfa_required).toBeUndefined();
  });

  it("serves an error scenario with its problem+json shape", async () => {
    setScenario("auth_login", "invalid_credentials");

    const res = await loginRequest();

    expect(res.status).toBe(401);
    const body = (await res.json()) as { code: string };
    expect(body.code).toBe("INVALID_CREDENTIALS");
  });
});
