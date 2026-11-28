import { useInfiniteQuery } from "@tanstack/react-query";
import { getApiClient } from "./client";
import type { components, operations } from "./schema";

export type Workflow = components["schemas"]["Workflow"];
type ListWorkflowsParams = NonNullable<
  operations["workflows_list"]["parameters"]["query"]
> & { workspaceId: string };

export async function listWorkflows(
  { workspaceId, cursor, limit, q }: ListWorkflowsParams,
  signal?: AbortSignal,
) {
  const { data } = await getApiClient().GET(
    "/api/v1/workspaces/{ws_id}/workflows",
    {
      params: { path: { ws_id: workspaceId }, query: { cursor, limit, q } },
      signal,
    },
  );
  if (!data) throw new Error("Missing workflows list response");
  return data;
}

export function useWorkflows(workspaceId: string, q?: string) {
  return useInfiniteQuery({
    queryKey: ["workflows", workspaceId, q],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam: cursor, signal }) =>
      listWorkflows({ workspaceId, cursor, q }, signal),
    getNextPageParam: (page) => page.next_cursor ?? undefined,
  });
}
