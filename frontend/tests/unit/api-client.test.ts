import { act, renderHook } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { getApiClient } from "../../src/lib/api/client";
import { useIdempotencyKey } from "../../src/lib/api/idempotency";
import { ApiError, isApiError } from "../../src/lib/api/problem";
import { server } from "../msw/server";
import { setScenario } from "../msw/scenarios";

const client = getApiClient();
const LOGIN_BODY = { email: "x", password: "y" };

function setCsrfCookie(value: string | null) {
  document.cookie = value
    ? `replora_csrf=${value}`
    : "replora_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
}

function postLogin(init?: { baseUrl?: string }) {
  return client.POST("/api/v1/auth/login", { ...init, body: LOGIN_BODY });
}

/** Mocks POST /auth/login's response for one test, bypassing fixtures. */
function mockLoginResponse(respond: () => Response) {
  server.use(http.post("/api/v1/auth/login", respond));
}

/** Calls postLogin() and returns the ApiError it's expected to throw. */
async function catchLoginError(): Promise<ApiError> {
  try {
    await postLogin();
  } catch (error) {
    if (isApiError(error)) return error;
    throw error;
  }
  throw new Error("expected the POST to throw");
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

    await postLogin();

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

    await postLogin();
    await postLogin();

    expect(csrfCalls).toBe(1);
  });

  it("omits X-CSRF-Token on a POST to an absolute URL on another origin", async () => {
    setCsrfCookie("test-token");
    let received: string | null | undefined;
    server.use(
      http.post(
        "https://storage.example.com/api/v1/auth/login",
        ({ request }) => {
          received = request.headers.get("x-csrf-token");
          return HttpResponse.json({ mfa_required: true }, { status: 200 });
        },
      ),
    );

    await postLogin({ baseUrl: "https://storage.example.com" });

    expect(received).toBeNull();
  });
});

describe("error passthrough", () => {
  it("throws ApiError with the problem+json code, never the detail field", async () => {
    setCsrfCookie("test-token");
    setScenario("auth_login", "invalid_credentials");

    const error = await catchLoginError();

    expect(error.problem.code).toBe("INVALID_CREDENTIALS");
  });

  it("throws ApiError for an HTML 502 (e.g. from an infra proxy)", async () => {
    setCsrfCookie("test-token");
    mockLoginResponse(
      () =>
        new HttpResponse("<html><body>Bad Gateway</body></html>", {
          status: 502,
          headers: { "content-type": "text/html" },
        }),
    );

    const error = await catchLoginError();

    expect(error.problem.status).toBe(502);
    expect(error.problem.code).toBe("INTERNAL_ERROR");
  });

  it("throws ApiError for an empty 500 body", async () => {
    setCsrfCookie("test-token");
    mockLoginResponse(() => new HttpResponse(null, { status: 500 }));

    const error = await catchLoginError();

    expect(error.problem.status).toBe(500);
    expect(error.problem.code).toBe("INTERNAL_ERROR");
  });

  it("throws ApiError with the FILE_TOO_LARGE code for a plain-text 413", async () => {
    setCsrfCookie("test-token");
    mockLoginResponse(
      () => new HttpResponse("request entity too large", { status: 413 }),
    );

    const error = await catchLoginError();

    expect(error.problem.status).toBe(413);
    expect(error.problem.code).toBe("FILE_TOO_LARGE");
  });

  it("falls back safely when a 4xx JSON body is not problem-shaped", async () => {
    setCsrfCookie("test-token");
    mockLoginResponse(() =>
      HttpResponse.json({ unexpected: "shape" }, { status: 400 }),
    );

    const error = await catchLoginError();

    expect(error.problem.status).toBe(400);
    expect(error.problem.code).toBe("INTERNAL_ERROR");
  });

  it("passes a normal 2xx JSON response through untouched", async () => {
    const { data } = await client.GET("/api/v1/auth/me");

    expect((data as { email?: string } | undefined)?.email).toBe(
      "salma@example.com",
    );
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
