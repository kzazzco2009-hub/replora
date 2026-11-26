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
 * only when the action itself restarts (e.g. a new `plan_hash`).
 */
export function useIdempotencyKey(): IdempotencyKey {
  const [value, setValue] = useState(() => crypto.randomUUID());
  return {
    value,
    reset: () => setValue(crypto.randomUUID()),
  };
}
