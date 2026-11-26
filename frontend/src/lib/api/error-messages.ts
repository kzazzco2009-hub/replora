import type { Problem } from "./problem";

/** `problem_codes` from contracts/error-codes.json. Keep in sync; the parity test checks it. */
export const PROBLEM_CODES = [
  "VALIDATION_FAILED",
  "NOT_FOUND",
  "METHOD_NOT_ALLOWED",
  "UNAUTHENTICATED",
  "INVALID_CREDENTIALS",
  "MFA_CHALLENGE_INVALID",
  "MFA_CODE_INVALID",
  "PASSWORD_INCORRECT",
  "TOKEN_INVALID",
  "CSRF_FAILED",
  "EMAIL_NOT_VERIFIED",
  "MFA_ALREADY_ENABLED",
  "MFA_NOT_ENABLED",
  "RATE_LIMITED",
  "FILE_TOO_LARGE",
  "QUOTA_EXCEEDED",
  "PERSONAL_WORKSPACE_UNDELETABLE",
  "PRECONDITION_FAILED",
  "PRECONDITION_REQUIRED",
  "DRAFT_INVALID",
  "PLAN_HASH_MISMATCH",
  "INVALID_STATE_TRANSITION",
  "IDEMPOTENCY_KEY_MISMATCH",
  "BASE_VERSION_STALE",
  "INTERNAL_ERROR",
  "NOT_IMPLEMENTED",
] as const;

export type ProblemCode = (typeof PROBLEM_CODES)[number];

/** Used when a response has no recognized `code` (including status-only failures with no problem body). */
export const GENERIC_ERROR_MESSAGE_KEY = "errors.generic";

/**
 * ProblemCode -> next-intl message key. A mapped type over `ProblemCode` so
 * removing or renaming a code here fails the TypeScript build.
 */
const PROBLEM_MESSAGE_KEYS: {
  readonly [K in ProblemCode]: `errors.problem.${K}`;
} = {
  VALIDATION_FAILED: "errors.problem.VALIDATION_FAILED",
  NOT_FOUND: "errors.problem.NOT_FOUND",
  METHOD_NOT_ALLOWED: "errors.problem.METHOD_NOT_ALLOWED",
  UNAUTHENTICATED: "errors.problem.UNAUTHENTICATED",
  INVALID_CREDENTIALS: "errors.problem.INVALID_CREDENTIALS",
  MFA_CHALLENGE_INVALID: "errors.problem.MFA_CHALLENGE_INVALID",
  MFA_CODE_INVALID: "errors.problem.MFA_CODE_INVALID",
  PASSWORD_INCORRECT: "errors.problem.PASSWORD_INCORRECT",
  TOKEN_INVALID: "errors.problem.TOKEN_INVALID",
  CSRF_FAILED: "errors.problem.CSRF_FAILED",
  EMAIL_NOT_VERIFIED: "errors.problem.EMAIL_NOT_VERIFIED",
  MFA_ALREADY_ENABLED: "errors.problem.MFA_ALREADY_ENABLED",
  MFA_NOT_ENABLED: "errors.problem.MFA_NOT_ENABLED",
  RATE_LIMITED: "errors.problem.RATE_LIMITED",
  FILE_TOO_LARGE: "errors.problem.FILE_TOO_LARGE",
  QUOTA_EXCEEDED: "errors.problem.QUOTA_EXCEEDED",
  PERSONAL_WORKSPACE_UNDELETABLE:
    "errors.problem.PERSONAL_WORKSPACE_UNDELETABLE",
  PRECONDITION_FAILED: "errors.problem.PRECONDITION_FAILED",
  PRECONDITION_REQUIRED: "errors.problem.PRECONDITION_REQUIRED",
  DRAFT_INVALID: "errors.problem.DRAFT_INVALID",
  PLAN_HASH_MISMATCH: "errors.problem.PLAN_HASH_MISMATCH",
  INVALID_STATE_TRANSITION: "errors.problem.INVALID_STATE_TRANSITION",
  IDEMPOTENCY_KEY_MISMATCH: "errors.problem.IDEMPOTENCY_KEY_MISMATCH",
  BASE_VERSION_STALE: "errors.problem.BASE_VERSION_STALE",
  INTERNAL_ERROR: "errors.problem.INTERNAL_ERROR",
  NOT_IMPLEMENTED: "errors.problem.NOT_IMPLEMENTED",
};

/** Exported for the parity test; not meant for other callers. */
export { PROBLEM_MESSAGE_KEYS };

function isProblemCode(code: string): code is ProblemCode {
  return (PROBLEM_CODES as readonly string[]).includes(code);
}

export interface MappedProblem {
  messageKey: string;
  correlationId: string | null;
}

/**
 * Maps a Problem to a message key and a correlation id, for the caller to
 * render and to look up translated text with. Never reads or returns
 * `problem.detail` (docs/api_contract.md §1): detail is server-internal text,
 * not something shown to users.
 */
export function mapProblem(problem: Problem): MappedProblem {
  const messageKey = isProblemCode(problem.code)
    ? PROBLEM_MESSAGE_KEYS[problem.code]
    : GENERIC_ERROR_MESSAGE_KEY;
  return { messageKey, correlationId: problem.correlation_id ?? null };
}
