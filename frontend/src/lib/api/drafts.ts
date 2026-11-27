import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { getApiClient } from "./client";
import type { components } from "./schema";

export type Template = components["schemas"]["Template"];
export type TemplateInput = components["schemas"]["TemplateInput"];
export type Draft = components["schemas"]["Draft"];
export type DraftCreateBody = components["schemas"]["DraftCreate"];

export const templatesQueryKey = ["templates"] as const;

/** `GET /templates` (public, cacheable): the TemplatePlanner's templates for the template picker. */
export function useTemplates(): UseQueryResult<Template[]> {
  return useQuery({
    queryKey: templatesQueryKey,
    queryFn: async () => {
      const { data } = await getApiClient().GET("/api/v1/templates");
      if (data === undefined) {
        throw new Error("GET /templates resolved with no data and no error");
      }
      return data;
    },
  });
}

export interface CreateDraftResult {
  draft: Draft;
  /** Send back as `If-Match` on `drafts_update` (PATCH). `null` if the response didn't set it. */
  etag: string | null;
}

export interface CreateDraftOptions {
  wsId: string;
  signal?: AbortSignal;
}

/**
 * `POST /workspaces/{ws_id}/drafts`. Error mapping is entirely the
 * existing machinery: `mapFieldErrors` for 422 (`body.template_id`,
 * `body.file_ids`, `body.file_ids.{i}` all arrive as ordinary `ProblemItem`s
 * and fall back to the generic validation message where there's no more
 * specific one), `mapProblem` for 404/429/501 and the rest.
 */
export async function createDraft(
  body: DraftCreateBody,
  { wsId, signal }: CreateDraftOptions,
): Promise<CreateDraftResult> {
  const { data, response } = await getApiClient().POST(
    "/api/v1/workspaces/{ws_id}/drafts",
    {
      params: { path: { ws_id: wsId } },
      body,
      signal,
    },
  );
  if (data === undefined) {
    throw new Error("drafts_create resolved with no data and no error");
  }
  return { draft: data, etag: response.headers.get("ETag") };
}
