const COOKIE_NAME = "replora_csrf";

function readCsrfCookie(): string | undefined {
  return document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${COOKIE_NAME}=`))
    ?.slice(COOKIE_NAME.length + 1);
}

let inFlight: Promise<string> | null = null;

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

  inFlight ??= fetch("/api/v1/auth/csrf", { credentials: "same-origin" })
    .then(() => {
      const token = readCsrfCookie();
      if (!token) {
        throw new Error("GET /auth/csrf did not set the replora_csrf cookie");
      }
      return token;
    })
    .finally(() => {
      inFlight = null;
    });

  return inFlight;
}
