import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "./client";
import { mapProblem } from "./error-messages";
import { isApiError } from "./problem";
import type { components, operations } from "./schema";

type RunLocation = { wsId: string; runId: string };
export type OutputLocation = RunLocation & { artifactId: string };
export type OutputArtifact = components["schemas"]["OutputArtifact"];
export type Lineage = components["schemas"]["Lineage"];
type Preview = components["schemas"]["Preview"];
export type PreviewPage = Omit<Preview, "rows"> & {
  rows: (Omit<Preview["rows"][number], "status"> & { status: string | null })[];
};
export type PreviewParams = NonNullable<
  operations["outputs_preview"]["parameters"]["query"]
>;
export type ResultStatus = NonNullable<PreviewParams["status"]>;
export const resultStatuses = [
  "matched",
  "value_diff",
  "missing_left",
  "missing_right",
] as const satisfies readonly ResultStatus[];

export function isResultStatus(status: string | null): status is ResultStatus {
  return resultStatuses.some((known) => known === status);
}

export function isTabular(output: OutputArtifact) {
  return (
    ["TabularArtifact", "ComparisonReport", "OutputFile"].includes(
      output.type,
    ) &&
    ["csv", "json"].includes(output.format.toLowerCase()) &&
    output.row_count != null
  );
}

const outputs = "/api/v1/workspaces/{ws_id}/runs/{run_id}/outputs";
const output = `${outputs}/{artifact_id}` as const;
function runPath({ wsId, runId }: RunLocation) {
  return { ws_id: wsId, run_id: runId };
}

export function outputPath(location: OutputLocation) {
  return { ...runPath(location), artifact_id: location.artifactId };
}

export function useOutputs(location: RunLocation) {
  return useQuery({
    queryKey: ["outputs", location],
    queryFn: async ({ signal }) => {
      const { data } = await getApiClient().GET(outputs, {
        params: { path: runPath(location) },
        signal,
      });
      if (!Array.isArray(data)) throw new Error("Unexpected outputs response");
      return data;
    },
  });
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function count(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

function isPreview(value: unknown): value is PreviewPage {
  if (
    !record(value) ||
    !count(value.total) ||
    !count(value.offset) ||
    !Array.isArray(value.columns) ||
    !Array.isArray(value.rows)
  )
    return false;
  const width = value.columns.length;
  return (
    value.columns.every(
      (column: unknown) =>
        record(column) &&
        typeof column.name === "string" &&
        typeof column.nullable === "boolean" &&
        ["string", "decimal", "integer", "date", "boolean"].some(
          (type) => column.type === type,
        ),
    ) &&
    value.rows.every(
      (row: unknown) =>
        record(row) &&
        count(row.row) &&
        (row.status === null || typeof row.status === "string") &&
        Array.isArray(row.cells) &&
        row.cells.length === width &&
        row.cells.every(
          (cell: unknown) =>
            cell === null ||
            typeof cell === "string" ||
            typeof cell === "boolean" ||
            (typeof cell === "number" && Number.isFinite(cell)),
        ),
    )
  );
}

export function useOutputPreview(
  location: OutputLocation,
  params: PreviewParams,
) {
  return useQuery({
    queryKey: ["output-preview", location, params],
    queryFn: async ({ signal }) => {
      try {
        const { data } = await getApiClient().GET(`${output}/preview`, {
          params: { path: outputPath(location), query: params },
          signal,
        });
        return isPreview(data) ? data : null;
      } catch (error) {
        if (isApiError(error) && [409, 422, 501].includes(error.problem.status))
          return null;
        throw error;
      }
    },
  });
}

export function useRowLineage(location: OutputLocation, row: number | null) {
  return useQuery({
    queryKey: ["row-lineage", location, row],
    enabled: row !== null,
    queryFn: async ({ signal }) => {
      if (row === null) throw new Error("Missing output row");
      const { data } = await getApiClient().GET(
        `${output}/rows/{row}/lineage`,
        {
          params: { path: { ...outputPath(location), row } },
          signal,
        },
      );
      if (
        !data ||
        !Array.isArray(data.sources) ||
        !Array.isArray(data.operations)
      )
        throw new Error("Unexpected lineage response");
      return data;
    },
  });
}

export function resultsErrorKey(error: unknown) {
  if (!isApiError(error)) return "results.requestFailed";
  return error.problem.status === 429
    ? "errors.problem.RATE_LIMITED"
    : mapProblem(error.problem).messageKey;
}
