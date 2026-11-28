import { describe, expect, it } from "vitest";
import { mapFieldErrors } from "../../src/lib/api/field-errors";
import type { Problem } from "../../src/lib/api/problem";

function problem(errors: Problem["errors"], detail?: string): Problem {
  return {
    type: "about:blank",
    title: "Validation failed",
    status: 422,
    code: "VALIDATION_FAILED",
    correlation_id: "corr-1",
    detail,
    errors,
  };
}

describe("mapFieldErrors", () => {
  it("strips the leading body. prefix to get the field name", () => {
    const result = mapFieldErrors(
      problem([{ path: "body.email", code: "INVALID_EMAIL", params: {} }]),
    );

    expect(Object.keys(result.fields)).toEqual(["email"]);
    expect(result.fields.email.messageKey).toBe(
      "errors.validation.INVALID_EMAIL",
    );
  });

  it("strips the leading query. prefix to get the field name", () => {
    const result = mapFieldErrors(
      problem([
        { path: "query.limit", code: "LESS_THAN_EQUAL", params: { le: 100 } },
      ]),
    );

    expect(Object.keys(result.fields)).toEqual(["limit"]);
    expect(result.fields.limit.params).toEqual({ le: 100 });
  });

  it("sends a path that is just body, query, or empty to form-level", () => {
    const result = mapFieldErrors(
      problem([
        { path: "body", code: "JSON_INVALID", params: {} },
        { path: "query", code: "MISSING", params: {} },
        { path: "", code: "MODEL_ATTRIBUTES_TYPE", params: {} },
      ]),
    );

    expect(Object.keys(result.fields)).toEqual([]);
    expect(result.form).toHaveLength(3);
    expect(result.form.map((e) => e.messageKey)).toEqual([
      "errors.validation.JSON_INVALID",
      "errors.validation.MISSING",
      "errors.validation.MODEL_ATTRIBUTES_TYPE",
    ]);
  });

  it("keeps the first error per field when more than one targets the same field", () => {
    const result = mapFieldErrors(
      problem([
        {
          path: "body.password",
          code: "STRING_TOO_SHORT",
          params: { min_length: 12 },
        },
        { path: "body.password", code: "STRING_TYPE", params: {} },
      ]),
    );

    expect(result.fields.password.messageKey).toBe(
      "errors.validation.STRING_TOO_SHORT",
    );
    expect(result.fields.password.params).toEqual({ min_length: 12 });
  });

  it("passes params through unchanged", () => {
    const result = mapFieldErrors(
      problem([
        {
          path: "body.code",
          code: "STRING_PATTERN_MISMATCH",
          params: { pattern: "^[0-9]{6}$" },
        },
      ]),
    );

    expect(result.fields.code.params).toEqual({ pattern: "^[0-9]{6}$" });
  });

  it("falls back to errors.validation.INVALID for an unknown code", () => {
    const result = mapFieldErrors(
      problem([{ path: "body.email", code: "SOME_FUTURE_CODE", params: {} }]),
    );

    expect(result.fields.email.messageKey).toBe("errors.validation.INVALID");
  });

  it("returns empty fields and form when there are no errors", () => {
    const result = mapFieldErrors(problem(null));

    expect(result.fields).toEqual({});
    expect(result.form).toEqual([]);
  });

  it("never reads problem.detail", () => {
    const result = mapFieldErrors(
      problem(
        [{ path: "body.email", code: "INVALID_EMAIL", params: {} }],
        "stack trace or internal path",
      ),
    );

    expect(JSON.stringify(result)).not.toContain("stack trace");
  });
});
