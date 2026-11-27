import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { getApiClient } from "../../src/lib/api/client";
import { ApiError, isApiError } from "../../src/lib/api/problem";
import { onSessionExpired, refreshSession } from "../../src/lib/api/session";
import { server } from "../msw/server";
import { setScenario } from "../msw/scenarios";

const client = getApiClient();
const LOGIN_BODY = { email: "x", password: "y" };
const UNAUTHENTICATED = {
  type: "about:blank",
  title: "Unauthorized",
  status: 401,
  code: "UNAUTHENTICATED",
  correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
};
const CSRF_FAILED = {
  type: "about:blank",
  title: "Forbidden",
  status: 403,
  code: "CSRF_FAILED",
  correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
};
function setCsrfCookie(value: string) {
  document.cookie = `replora_csrf=${value}`;
}

async function catchMeError(): Promise<ApiError> {
  try {
    await client.GET("/api/v1/auth/me");
  } catch (error) {
    if (isApiError(error)) return error;
    throw error;
  }
  throw new Error("expected the GET to throw");
}

async function catchLoginError(): Promise<ApiError> {
  try {
    await client.POST("/api/v1/auth/login", { body: LOGIN_BODY });
  } catch (error) {
    if (isApiError(error)) return error;
    throw error;
  }
  throw new Error("expected the POST to throw");
}
beforeEach(() => setCsrfCookie("test-token"));
describe("401 UNAUTHENTICATED -> refresh -> retry once", () => {
  it("retries once after one refresh; the retried success reaches the caller (proves order: errorMiddleware never throws)", async () => {
    let meCalls = 0,
      refreshCalls = 0;
    server.use(
      http.get(
        "/api/v1/auth/me",
        () => {
          meCalls += 1;
          return HttpResponse.json(UNAUTHENTICATED, { status: 401 });
        },
        { once: true },
      ),
      http.post("/api/v1/auth/refresh", () => {
        refreshCalls += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const { data, error } = await client.GET("/api/v1/auth/me");
    expect(error).toBeUndefined();
    expect((data as { email?: string } | undefined)?.email).toBe(
      "salma@example.com",
    );
    expect(meCalls).toBe(1);
    expect(refreshCalls).toBe(1);
  });

  it("shares one refresh call across 5 concurrent 401s, then retries all 5", async () => {
    let meCalls = 0,
      refreshCalls = 0;
    server.use(
      http.get("/api/v1/auth/me", () => {
        meCalls += 1;
        return meCalls <= 5
          ? HttpResponse.json(UNAUTHENTICATED, { status: 401 })
          : HttpResponse.json({ email: "salma@example.com" }, { status: 200 });
      }),
      http.post("/api/v1/auth/refresh", () => {
        refreshCalls += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    const results = await Promise.all(
      Array.from({ length: 5 }, () => client.GET("/api/v1/auth/me")),
    );
    expect(refreshCalls).toBe(1);
    expect(meCalls).toBe(10);
    for (const { data, error } of results) {
      expect(error).toBeUndefined();
      expect((data as { email?: string } | undefined)?.email).toBe(
        "salma@example.com",
      );
    }
  });

  it("does not retry when the refresh itself returns 401; notifies session-expired once", async () => {
    let meCalls = 0,
      refreshCalls = 0;
    server.use(
      http.get("/api/v1/auth/me", () => {
        meCalls += 1;
        return HttpResponse.json(UNAUTHENTICATED, { status: 401 });
      }),
      http.post("/api/v1/auth/refresh", () => {
        refreshCalls += 1;
        return HttpResponse.json(UNAUTHENTICATED, { status: 401 });
      }),
    );
    let expiredCalls = 0;
    const unsubscribe = onSessionExpired(() => (expiredCalls += 1));
    expect((await catchMeError()).problem.code).toBe("UNAUTHENTICATED");
    unsubscribe();
    expect(meCalls).toBe(1);
    expect(refreshCalls).toBe(1);
    expect(expiredCalls).toBe(1);
  });

  it("never refreshes for login's INVALID_CREDENTIALS or mfa-challenge's MFA_CHALLENGE_INVALID", async () => {
    let refreshCalls = 0;
    server.use(
      http.post("/api/v1/auth/refresh", () => {
        refreshCalls += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    setScenario("auth_login", "invalid_credentials");
    expect((await catchLoginError()).problem.code).toBe("INVALID_CREDENTIALS");
    let challengeError: ApiError | undefined;
    setScenario("auth_mfa_challenge", "challenge_invalid");
    try {
      await client.POST("/api/v1/auth/mfa/challenge", {
        body: { code: "123456" },
      });
    } catch (caught) {
      if (isApiError(caught)) challengeError = caught;
    }
    expect(challengeError?.problem.code).toBe("MFA_CHALLENGE_INVALID");
    expect(refreshCalls).toBe(0);
  });

  it("does not refresh again when the retried request gets 401 again (no loop)", async () => {
    let meCalls = 0,
      refreshCalls = 0;
    server.use(
      http.get("/api/v1/auth/me", () => {
        meCalls += 1;
        return HttpResponse.json(UNAUTHENTICATED, { status: 401 });
      }),
      http.post("/api/v1/auth/refresh", () => {
        refreshCalls += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    expect((await catchMeError()).problem.code).toBe("UNAUTHENTICATED");
    expect(meCalls).toBe(2);
    expect(refreshCalls).toBe(1);
  });

  it("carries X-CSRF-Token on the refresh itself; never re-refreshes for /auth/refresh's or /auth/csrf's own 401", async () => {
    let refreshToken: string | null = null;
    server.use(
      http.post("/api/v1/auth/refresh", ({ request }) => {
        refreshToken = request.headers.get("x-csrf-token");
        return new HttpResponse(null, { status: 204 });
      }),
    );
    expect(await refreshSession()).toBe(true);
    expect(refreshToken).toBe("test-token");
    let refreshCalls = 0;
    server.use(
      http.post("/api/v1/auth/refresh", () => {
        refreshCalls += 1;
        return HttpResponse.json(UNAUTHENTICATED, { status: 401 });
      }),
    );
    await expect(client.POST("/api/v1/auth/refresh")).rejects.toThrow();
    expect(refreshCalls).toBe(1); // no refresh-seeking second call to itself
    let csrfGetCalls = 0;
    server.use(
      http.get("/api/v1/auth/csrf", () => {
        csrfGetCalls += 1;
        return HttpResponse.json(UNAUTHENTICATED, { status: 401 });
      }),
    );
    await expect(client.GET("/api/v1/auth/csrf")).rejects.toThrow();
    expect(csrfGetCalls).toBe(1);
    expect(refreshCalls).toBe(1);
  });
});
describe("403 CSRF_FAILED -> fresh token -> retry once", () => {
  it("retries once with a fresh CSRF token, resending body and Idempotency-Key unchanged", async () => {
    setCsrfCookie("stale-token");
    let csrfCalls = 0,
      loginCalls = 0;
    const seenTokens: Array<string | null> = [];
    const seenIdempotencyKeys: Array<string | null> = [];
    server.use(
      http.get("/api/v1/auth/csrf", () => {
        csrfCalls += 1;
        document.cookie = "replora_csrf=fresh-token";
        return new HttpResponse(null, { status: 204 });
      }),
      http.post("/api/v1/auth/login", ({ request }) => {
        loginCalls += 1;
        seenTokens.push(request.headers.get("x-csrf-token"));
        seenIdempotencyKeys.push(request.headers.get("idempotency-key"));
        return loginCalls === 1
          ? HttpResponse.json(CSRF_FAILED, { status: 403 })
          : HttpResponse.json({ mfa_required: true }, { status: 200 });
      }),
    );
    const { data, error } = await client.POST("/api/v1/auth/login", {
      body: LOGIN_BODY,
      headers: { "Idempotency-Key": "fixed-key" },
    });
    expect(error).toBeUndefined();
    expect(data).toEqual({ mfa_required: true });
    expect(loginCalls).toBe(2);
    expect(csrfCalls).toBe(1);
    expect(seenTokens).toEqual(["stale-token", "fresh-token"]);
    expect(seenIdempotencyKeys).toEqual(["fixed-key", "fixed-key"]);
  });

  it("surfaces a second CSRF_FAILED as ApiError, without a second retry", async () => {
    setCsrfCookie("stale-token");
    let csrfCalls = 0;
    server.use(
      http.get("/api/v1/auth/csrf", () => {
        csrfCalls += 1;
        document.cookie = "replora_csrf=also-stale";
        return new HttpResponse(null, { status: 204 });
      }),
      http.post("/api/v1/auth/login", () =>
        HttpResponse.json(CSRF_FAILED, { status: 403 }),
      ),
    );
    expect((await catchLoginError()).problem.code).toBe("CSRF_FAILED");
    expect(csrfCalls).toBe(1);
  });
});
