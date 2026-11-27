import type { Problem } from "./problem";

/** `validation_codes` from contracts/error-codes.json. Keep in sync; the parity test checks it. */
export const VALIDATION_CODES = [
  "MISSING",
  "EXTRA_FORBIDDEN",
  "JSON_INVALID",
  "MODEL_ATTRIBUTES_TYPE",
  "STRING_TYPE",
  "STRING_TOO_SHORT",
  "STRING_TOO_LONG",
  "STRING_PATTERN_MISMATCH",
  "LITERAL_ERROR",
  "UUID_PARSING",
  "INVALID_EMAIL",
  "MFA_CODE_OR_RECOVERY_REQUIRED",
  "INT_PARSING",
  "INT_FROM_FLOAT",
  "GREATER_THAN",
  "GREATER_THAN_EQUAL",
  "LESS_THAN_EQUAL",
  "TOO_SHORT",
  "TOO_LONG",
  "INVALID",
] as const;

export type ValidationCode = (typeof VALIDATION_CODES)[number];

/** Used when a field error's `code` isn't one of `VALIDATION_CODES`. */
export const GENERIC_VALIDATION_MESSAGE_KEY = "errors.validation.INVALID";

const VALIDATION_MESSAGE_KEYS: {
  readonly [K in ValidationCode]: `errors.validation.${K}`;
} = Object.fromEntries(
  VALIDATION_CODES.map((code) => [code, `errors.validation.${code}`]),
) as never;

function isValidationCode(code: string): code is ValidationCode {
  return (VALIDATION_CODES as readonly string[]).includes(code);
}

export interface FieldError {
  messageKey: string;
  params: Record<string, unknown>;
}

export interface MappedFieldErrors {
  fields: Record<string, FieldError>;
  form: FieldError[];
}

/** Strips a leading "body." / "query." segment; "body"/"query"/"" means form-level. */
function fieldName(path: string): string | null {
  if (path === "" || path === "body" || path === "query") return null;
  for (const prefix of ["body.", "query."]) {
    if (path.startsWith(prefix)) return path.slice(prefix.length);
  }
  return path;
}

function toFieldError(
  code: string,
  params: Record<string, unknown>,
): FieldError {
  return {
    messageKey: isValidationCode(code)
      ? VALIDATION_MESSAGE_KEYS[code]
      : GENERIC_VALIDATION_MESSAGE_KEY,
    params,
  };
}

/**
 * Maps `problem.errors[]` ({path, code, params}) to per-field messages and
 * form-level messages. Never reads `problem.detail` (docs/api_contract.md
 * §1): detail is server-internal text, not something shown to users.
 */
export function mapFieldErrors(problem: Problem): MappedFieldErrors {
  const fields: Record<string, FieldError> = {};
  const form: FieldError[] = [];

  for (const item of problem.errors ?? []) {
    const params = (item.params ?? {}) as Record<string, unknown>;
    const name = fieldName(item.path);
    if (name === null) {
      form.push(toFieldError(item.code, params));
    } else if (!(name in fields)) {
      fields[name] = toFieldError(item.code, params);
    }
  }

  return { fields, form };
}
