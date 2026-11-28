import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "./client";
import { mapProblem } from "./error-messages";
import { mapFieldErrors } from "./field-errors";
import { isApiError } from "./problem";
import type { components } from "./schema";

export type Run = components["schemas"]["Run"];
export type RunIssue = components["schemas"]["Issue"];
export type Operation = components["schemas"]["OperationContract"];

interface RunWrite {
  wsId: string;
  idempotencyKey: string;
}

export async function createRun(
  draftId: string,
  options: RunWrite,
): Promise<Run> {
  const { data } = await getApiClient().POST(
    "/api/v1/workspaces/{ws_id}/runs",
    {
      params: {
        path: { ws_id: options.wsId },
        header: { "Idempotency-Key": options.idempotencyKey },
      },
      body: { draft_id: draftId },
    },
  );
  if (!data) throw new Error("Missing run response");
  return data;
}

export const runQueryKey = (wsId: string, runId: string) =>
  ["run", wsId, runId] as const;

export function useRun(
  wsId: string,
  runId: string,
  { pollApproval = false } = {},
) {
  return useQuery<Run>({
    queryKey: runQueryKey(wsId, runId),
    refetchInterval: ({ state }) =>
      pollApproval && state.data?.state === "AWAITING_APPROVAL" ? 5_000 : false,
    queryFn: async ({ signal }) => {
      const { data } = await getApiClient().GET(
        "/api/v1/workspaces/{ws_id}/runs/{run_id}",
        {
          params: { path: { ws_id: wsId, run_id: runId } },
          signal,
        },
      );
      if (!data) throw new Error("Missing run response");
      return data;
    },
  });
}

export async function approveRun(
  runId: string,
  planHash: string,
  options: RunWrite,
): Promise<Run> {
  const { data } = await getApiClient().POST(
    "/api/v1/workspaces/{ws_id}/runs/{run_id}/approve",
    {
      params: {
        path: { ws_id: options.wsId, run_id: runId },
        header: { "Idempotency-Key": options.idempotencyKey },
      },
      body: { plan_hash: planHash },
    },
  );
  if (!data) throw new Error("Missing approved run response");
  return data;
}

// TODO: Replace these local types with generated types once #134 is in the schema.
type JsonScalar = string | number | boolean | null;
type ReviewOption =
  JsonScalar | ReviewOption[] | { [key: string]: ReviewOption };
type ReviewChoice = Pick<RunIssue, "code" | "path"> & { value: ReviewOption };
type ResolveRequest = { plan_hash: string; choices: ReviewChoice[] };
type ResolveInput = Pick<ResolveRequest, "choices"> & {
  planHash: string;
  idempotencyKey: string;
};

export function reviewOptions(issue: RunIssue): ReviewOption[] | undefined {
  const options = issue.params?.options;
  return Array.isArray(options) ? (options as ReviewOption[]) : undefined;
}

export async function resolveRun(
  wsId: string,
  runId: string,
  { planHash, choices, idempotencyKey }: ResolveInput,
): Promise<Run> {
  const body: ResolveRequest = { plan_hash: planHash, choices };
  const { data } = await getApiClient().POST(
    "/api/v1/workspaces/{ws_id}/runs/{run_id}/resolve",
    {
      params: {
        path: { ws_id: wsId, run_id: runId },
        header: { "Idempotency-Key": idempotencyKey },
      },
      body,
    },
  );
  if (!data) throw new Error("Missing resolved run response");
  return data;
}

export function useOperations() {
  return useQuery({
    queryKey: ["operations"],
    queryFn: async ({ signal }) => {
      const { data } = await getApiClient().GET("/api/v1/operations", {
        signal,
      });
      if (!data) throw new Error("Missing operations response");
      return data;
    },
  });
}

export async function cancelRun(wsId: string, runId: string): Promise<Run> {
  const { data } = await getApiClient().POST(
    "/api/v1/workspaces/{ws_id}/runs/{run_id}/cancel",
    { params: { path: { ws_id: wsId, run_id: runId } } },
  );
  if (!data) throw new Error("Missing cancelled run response");
  return data;
}

export function progressErrorKey(error: unknown) {
  if (!isApiError(error)) return "runProgress.requestFailed";
  return error.problem.status === 429
    ? "errors.problem.RATE_LIMITED"
    : mapProblem(error.problem).messageKey;
}

export function runErrorMessages(error: unknown) {
  if (!isApiError(error)) return [{ messageKey: "runReview.requestFailed" }];
  if (error.problem.status === 429) {
    return [{ messageKey: "errors.problem.RATE_LIMITED" }];
  }
  const message = mapProblem(error.problem);
  if (error.problem.status !== 422) return [message];

  const fields = mapFieldErrors(error.problem);
  return [message, ...fields.form, ...Object.values(fields.fields)];
}
