import { act, renderHook } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { getApiClient } from "../../src/lib/api/client";
import { useIdempotencyKey } from "../../src/lib/api/idempotency";
import { isApiError } from "../../src/lib/api/problem";
import { server } from "../msw/server";
import { setScenario } from "../msw/scenarios";

const client = getApiClient();

function setCsrfCookie(value: string | null) {
  document.cookie = value
    ? `replora_csrf=${value}`
    : "replora_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}

beforeEach(() => {
  setCsrfCookie(null);
});

describe("CSRF header injection", () => {
  it("sends X-CSRF-Token on an unsafe method", async () => {
    setCsrfCookie("test-token");
    let received: string | null = null;
    server.use(
      http.post("/api/v1/auth/login", ({ request }) => {
        received = request.headers.get("x-csrf-token");
        return HttpResponse.json({ mfa_required: true }, { status: 200 });
      }),
    );

    await client.POST("/api/v1/auth/login", {
      body: { email: "salma@example.com", password: "x" },
    });

    expect(received).toBe("test-token");
  });

  it("never sends X-CSRF-Token on GET", async () => {
    setCsrfCookie("test-token");
    let received: string | null | undefined;
    server.use(
      http.get("/api/v1/auth/me", ({ request }) => {
        received = request.headers.get("x-csrf-token");
        return new HttpResponse(null, { status: 401 });
      }),
    );

    await expect(client.GET("/api/v1/auth/me")).rejects.toThrow();
    expect(received).toBeNull();
  });

  it("bootstraps the cookie with one GET /auth/csrf before unsafe calls, when it's missing", async () => {
    let csrfCalls = 0;
    server.use(
      http.get("/api/v1/auth/csrf", () => {
        csrfCalls += 1;
        document.cookie = "replora_csrf=bootstrapped";
        return new HttpResponse(null, { status: 204 });
      }),
      http.post("/api/v1/auth/login", () =>
        HttpResponse.json({ mfa_required: true }, { status: 200 }),
      ),
    );

    await client.POST("/api/v1/auth/login", {
      body: { email: "x", password: "y" },
    });
    await client.POST("/api/v1/auth/login", {
      body: { email: "x", password: "y" },
    });

    expect(csrfCalls).toBe(1);
  });
});

describe("error passthrough", () => {
  it("throws ApiError with the problem+json code, never the detail field", async () => {
    setCsrfCookie("test-token");
    setScenario("auth_login", "invalid_credentials");

    let caught: unknown;
    try {
      await client.POST("/api/v1/auth/login", {
        body: { email: "x", password: "y" },
      });
    } catch (error) {
      caught = error;
    }

    if (!isApiError(caught)) throw new Error("expected an ApiError");
    expect(caught.problem.code).toBe("INVALID_CREDENTIALS");
  });
});

describe("useIdempotencyKey", () => {
  it("returns a stable UUID across re-renders, and a new one after reset", () => {
    const { result, rerender } = renderHook(() => useIdempotencyKey());
    const first = result.current.value;

    rerender();
    expect(result.current.value).toBe(first);

    act(() => {
      result.current.reset();
    });
    expect(result.current.value).not.toBe(first);
  });
});
