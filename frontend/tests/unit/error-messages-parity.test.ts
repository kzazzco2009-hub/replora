import { describe, expect, it } from "vitest";
import errorCodes from "../../../contracts/error-codes.json";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import {
  GENERIC_ERROR_MESSAGE_KEY,
  mapProblem,
  PROBLEM_CODES,
  PROBLEM_MESSAGE_KEYS,
} from "../../src/lib/api/error-messages";
import type { Problem } from "../../src/lib/api/problem";

function problem(code: string): Problem {
  return {
    type: "about:blank",
    title: code,
    status: 400,
    code,
    correlation_id: "corr-1",
  };
}

describe("error-messages vs contracts/error-codes.json", () => {
  it("maps exactly the contract's problem_codes, no more and no fewer", () => {
    expect([...PROBLEM_CODES].sort()).toEqual(
      Object.keys(errorCodes.problem_codes).sort(),
    );
  });

  it("validation_codes are allow-listed (field-level, not mapped in this PR)", () => {
    const allowListed = [
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
    ];
    expect(Object.keys(errorCodes.validation_codes).sort()).toEqual(
      allowListed.sort(),
    );
  });

  it("rejection_codes are allow-listed (field-level, not mapped in this PR)", () => {
    const allowListed = [
      "FILE_EMPTY",
      "FILE_SIZE_MISMATCH",
      "FILE_TYPE_UNSUPPORTED",
      "FILE_CORRUPT",
      "ZIP_ENCRYPTED",
      "ZIP_TOO_MANY_MEMBERS",
      "ZIP_TOO_LARGE",
      "ZIP_RATIO_EXCEEDED",
      "ZIP_NESTED",
      "ZIP_UNSAFE_PATH",
      "ZIP_SYMLINK",
      "ZIP_MEMBER_UNSUPPORTED",
    ];
    expect(Object.keys(errorCodes.rejection_codes).sort()).toEqual(
      allowListed.sort(),
    );
  });
});

describe("error message keys exist in both locales", () => {
  it.each(PROBLEM_CODES)("en.json has errors.problem.%s", (code) => {
    expect(en.errors.problem).toHaveProperty(code);
  });

  it.each(PROBLEM_CODES)("ar.json has errors.problem.%s", (code) => {
    expect(ar.errors.problem).toHaveProperty(code);
  });

  it("en.json and ar.json have the generic fallback key", () => {
    expect(en.errors.generic).toBeTruthy();
    expect(ar.errors.generic).toBeTruthy();
  });
});

describe("mapProblem", () => {
  it("maps a known code to its message key and passes the correlation id through", () => {
    const result = mapProblem(problem("NOT_FOUND"));
    expect(result).toEqual({
      messageKey: PROBLEM_MESSAGE_KEYS.NOT_FOUND,
      correlationId: "corr-1",
    });
  });

  it("falls back to the generic key for an unknown code", () => {
    const result = mapProblem(problem("SOME_FUTURE_CODE"));
    expect(result.messageKey).toBe(GENERIC_ERROR_MESSAGE_KEY);
  });

  it("never reads problem.detail", () => {
    const withDetail: Problem = {
      ...problem("NOT_FOUND"),
      detail: "stack trace or internal path",
    };
    const result = mapProblem(withDetail);
    expect(JSON.stringify(result)).not.toContain("stack trace");
  });
});
