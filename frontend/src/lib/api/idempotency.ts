"use client";

import { useState } from "react";

export interface IdempotencyKey {
  readonly value: string;
  reset: () => void;
}

/**
 * One UUID per user action (api_contract.md §1): required on
 * `POST /workspaces/{ws}/runs` and `POST /workspaces/{ws}/runs/{id}/approve`.
 * Stable across re-renders and retries of the same action. Call `reset()`
 * whenever the action itself changes — not just on a new `plan_hash`, but
 * on any change to the request body too (different files, another draft):
 * reusing a key with a different body gets 409 IDEMPOTENCY_KEY_MISMATCH.
 */
export function useIdempotencyKey(): IdempotencyKey {
  const [value, setValue] = useState(() => crypto.randomUUID());
  return {
    value,
    reset: () => setValue(crypto.randomUUID()),
  };
}
