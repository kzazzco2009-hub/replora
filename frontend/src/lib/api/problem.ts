import type { components } from "./schema";

export type Problem = components["schemas"]["ProblemDetails"];

export class ApiError extends Error {
  readonly problem: Problem;

  constructor(
    problem: Problem,
    readonly retryAfter = "",
  ) {
    super(problem.title);
    this.name = "ApiError";
    this.problem = problem;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
