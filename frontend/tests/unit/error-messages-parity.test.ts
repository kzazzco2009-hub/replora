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
import { VALIDATION_CODES } from "../../src/lib/api/field-errors";
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

  it("maps exactly the contract's validation_codes, no more and no fewer", () => {
    expect([...VALIDATION_CODES].sort()).toEqual(
      Object.keys(errorCodes.validation_codes).sort(),
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

  it.each(VALIDATION_CODES)("en.json has errors.validation.%s", (code) => {
    expect(en.errors.validation).toHaveProperty(code);
  });

  it.each(VALIDATION_CODES)("ar.json has errors.validation.%s", (code) => {
    expect(ar.errors.validation).toHaveProperty(code);
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
