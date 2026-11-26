import createClient from "openapi-fetch";
import type { Middleware } from "openapi-fetch";
import { ensureCsrfToken } from "./csrf";
import { ApiError, type Problem } from "./problem";
import type { paths } from "./schema";

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/**
 * X-CSRF-Token isn't a typed header in openapi.json (api_contract.md §1
 * documents it in prose only), so it's added here on the raw Request the
 * typed call already built, not through the generated types.
 */
const csrfMiddleware: Middleware = {
  async onRequest({ request }) {
    if (!UNSAFE_METHODS.has(request.method)) return;
    // The one request this client could ever send to another origin is
    // the direct-to-storage upload PUT (S-65, a Supabase signed URL in
    // production). That origin never checks X-CSRF-Token, and sending it
    // would turn a simple upload into a CORS-preflighted request, so the
    // header is same-origin only.
    if (new URL(request.url).origin !== location.origin) return;
    const token = await ensureCsrfToken();
    request.headers.set("X-CSRF-Token", token);
  },
};

const FALLBACK_CODE_BY_STATUS: Record<number, string> = {
  413: "FILE_TOO_LARGE",
  429: "RATE_LIMITED",
};

function isProblem(value: unknown): value is Problem {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { code?: unknown }).code === "string"
  );
}

function buildFallbackProblem(response: Response): Problem {
  return {
    type: "about:blank",
    title: response.statusText || "Unexpected error",
    status: response.status,
    code: FALLBACK_CODE_BY_STATUS[response.status] ?? "INTERNAL_ERROR",
  };
}

/**
 * Every non-2xx response (except 304, which isn't an error — api_contract.md
 * §1) is meant to be `application/problem+json`, but one that never reached
 * the backend (a 502/504 from an infra proxy, a 413 from an upstream body
 * -size limit, an empty body) might not be — and even a parsed JSON body
 * might not be problem-shaped. Falling back to a minimal Problem, using a
 * status-matched code from error-codes.json where one exists (413 ->
 * FILE_TOO_LARGE, 429 -> RATE_LIMITED) and INTERNAL_ERROR otherwise — never
 * an invented code — means every caller gets an ApiError either way, never
 * a raw JSON parse error or an unrelated body passed through as if it were
 * one. `problem.detail` is never read for display anywhere.
 */
const errorMiddleware: Middleware = {
  async onResponse({ response }) {
    if (response.ok || response.status === 304) return;

    let problem: Problem;
    try {
      const body: unknown = await response.json();
      problem = isProblem(body) ? body : buildFallbackProblem(response);
    } catch {
      problem = buildFallbackProblem(response);
    }
    throw new ApiError(problem);
  },
};

type ApiClient = ReturnType<typeof createClient<paths>>;

let instance: ApiClient | undefined;

/**
 * Built lazily, not at module scope: a "use client" component's module
 * is still imported during SSR (just not rendered there), where
 * `location` doesn't exist — evaluating `location.origin` at import time
 * would throw a ReferenceError on the server.
 *
 * openapi-fetch builds a `Request` directly rather than calling `fetch()`
 * with a relative URL, so `baseUrl` must be an absolute origin — a plain
 * relative string throws. `location.origin` is always same-origin by
 * construction, matching api_contract.md §1. Every generated path already
 * starts with /api/v1 (the schema's server path).
 */
export function getApiClient(): ApiClient {
  if (!instance) {
    instance = createClient<paths>({
      baseUrl: location.origin,
      credentials: "same-origin",
      // openapi-fetch resolves `fetch` once, at client-creation time.
      // MSW's setupServer patches globalThis.fetch in tests/setup.ts's
      // beforeAll, which runs after this lazy factory's first call in a
      // given test file — capturing `fetch` directly would still risk
      // missing that patch depending on call order. Re-reading
      // globalThis.fetch per call avoids that, with no cost in
      // production, where fetch is never patched after module load.
      fetch: (request) => globalThis.fetch(request),
    });
    instance.use(csrfMiddleware, errorMiddleware);
  }
  return instance;
}
