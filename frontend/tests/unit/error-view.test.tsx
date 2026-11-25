import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ErrorView } from "../../src/components/error-view";
import { ApiError, type Problem } from "../../src/lib/api/problem";

function problem(overrides: Partial<Problem> = {}): Problem {
  return {
    type: "about:blank",
    title: "Validation failed",
    status: 422,
    code: "VALIDATION_FAILED",
    detail: "super secret stack detail",
    correlation_id: "01J000000000000000000000",
    errors: null,
    ...overrides,
  };
}

describe("ErrorView", () => {
  it("shows the correlation_id for an ApiError that has one", () => {
    render(<ErrorView error={new ApiError(problem())} reset={() => {}} />);
    expect(screen.getByText("01J000000000000000000000")).toBeTruthy();
  });

  it("shows no reference line for an ApiError without a correlation_id (ar)", () => {
    render(
      <ErrorView
        error={new ApiError(problem({ correlation_id: null }))}
        reset={() => {}}
        lang="ar"
      />,
    );
    expect(screen.queryByTestId("error-reference")).toBeNull();
  });

  it("shows the digest for a plain Error that has one", () => {
    const error = Object.assign(new Error("boom"), { digest: "abc123" });
    render(<ErrorView error={error} reset={() => {}} />);
    expect(screen.getByText("abc123")).toBeTruthy();
  });

  it("never renders the problem detail or the raw error message", () => {
    render(<ErrorView error={new ApiError(problem())} reset={() => {}} />);
    expect(screen.queryByText(/super secret stack detail/)).toBeNull();

    render(
      <ErrorView error={new Error("do not show this")} reset={() => {}} />,
    );
    expect(screen.queryByText(/do not show this/)).toBeNull();
  });

  it("calls reset when the retry button is clicked", () => {
    const reset = vi.fn();
    render(<ErrorView error={new Error("boom")} reset={reset} />);
    fireEvent.click(screen.getByRole("button"));
    expect(reset).toHaveBeenCalledOnce();
  });
});
