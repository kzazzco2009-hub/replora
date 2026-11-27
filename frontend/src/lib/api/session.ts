import { ensureCsrfToken } from "./csrf";

type SessionExpiredHandler = () => void;

const sessionExpiredHandlers = new Set<SessionExpiredHandler>();

function notifySessionExpired(): void {
  for (const handler of sessionExpiredHandlers) handler();
}

/** Registers a session-expired handler. Returns an unsubscribe function. */
export function onSessionExpired(handler: SessionExpiredHandler): () => void {
  sessionExpiredHandlers.add(handler);
  return () => sessionExpiredHandlers.delete(handler);
}

let inFlight: Promise<boolean> | null = null;

async function doRefresh(): Promise<boolean> {
  try {
    const token = await ensureCsrfToken();
    const response = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRF-Token": token },
    });
    if (response.status === 204) return true;
    if (response.status === 401) notifySessionExpired();
    return false;
  } catch {
    return false;
  }
}

/**
 * POSTs `/api/v1/auth/refresh` with a plain `fetch`. Single-flight: the
 * refresh token rotates, so concurrent 401s must share one in-flight
 * refresh. Resolves `true` on 204, `false` otherwise, notifying
 * `onSessionExpired` once on a 401 (session gone).
 */
export async function refreshSession(): Promise<boolean> {
  inFlight ??= doRefresh().finally(() => {
    inFlight = null;
  });
  return inFlight;
}
