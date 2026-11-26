const COOKIE_NAME = "replora_csrf";

function readCsrfCookie(): string | undefined {
  return document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${COOKIE_NAME}=`))
    ?.slice(COOKIE_NAME.length + 1);
}

function fetchCsrfToken(): Promise<string> {
  return fetch("/api/v1/auth/csrf", { credentials: "same-origin" }).then(() => {
    const token = readCsrfCookie();
    if (!token) {
      throw new Error("GET /auth/csrf did not set the replora_csrf cookie");
    }
    return token;
  });
}

let ensureInFlight: Promise<string> | null = null;

/**
 * Returns the readable `replora_csrf` cookie's value, fetching it first
 * (`GET /auth/csrf`) if missing. Concurrent callers share one in-flight
 * fetch. Uses a plain `fetch`, not the typed client, since this is the
 * one endpoint CSRF protection doesn't apply to (api_contract.md §2) and
 * the typed client's own CSRF middleware calls this function.
 */
export async function ensureCsrfToken(): Promise<string> {
  const existing = readCsrfCookie();
  if (existing) return existing;

  ensureInFlight ??= fetchCsrfToken().finally(() => {
    ensureInFlight = null;
  });

  return ensureInFlight;
}

let refreshInFlight: Promise<string> | null = null;

/**
 * Always re-fetches `GET /auth/csrf`, bypassing the cached cookie, for
 * recovery after a 403 `CSRF_FAILED`. Single-flight like `ensureCsrfToken`,
 * but its own flight: this is a deliberate refresh, not a bootstrap.
 */
export async function refreshCsrfToken(): Promise<string> {
  refreshInFlight ??= fetchCsrfToken().finally(() => {
    refreshInFlight = null;
  });

  return refreshInFlight;
}
