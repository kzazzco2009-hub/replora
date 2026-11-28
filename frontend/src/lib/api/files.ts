import { useInfiniteQuery } from "@tanstack/react-query";
import { getApiClient } from "./client";
import type { components, operations } from "./schema";
import type { UploadedFile } from "./upload";

export type FileType = NonNullable<UploadedFile["detected_type"]>;
type FilesQuery = NonNullable<operations["files_list"]["parameters"]["query"]>;
type ListFilesParams = Omit<FilesQuery, "type"> & {
  workspaceId: string;
  type?: FileType | null;
};
type FilePage = Omit<components["schemas"]["FilePage"], "items"> & {
  items: UploadedFile[];
};

export async function listFiles(
  { workspaceId, cursor, limit, type }: ListFilesParams,
  signal?: AbortSignal,
): Promise<FilePage> {
  const { data } = await getApiClient().GET(
    "/api/v1/workspaces/{ws_id}/files",
    {
      params: {
        path: { ws_id: workspaceId },
        // Main's generated query enum omits JSON. Send the selected type verbatim.
        query: { cursor, limit, type: type as FilesQuery["type"] },
      },
      signal,
    },
  );
  if (!data) throw new Error("Missing files list response");
  return data;
}

export function useFiles(workspaceId: string, type?: FileType) {
  return useInfiniteQuery({
    queryKey: ["files", workspaceId, type],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam: cursor, signal }) =>
      listFiles({ workspaceId, cursor, type }, signal),
    getNextPageParam: (page) => page.next_cursor ?? undefined,
  });
}
