import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { getApiClient } from "./client";
import type { components } from "./schema";

export type Me = components["schemas"]["Me"];

export const meQueryKey = ["me"] as const;

/**
 * The current user and their workspace memberships (GET /auth/me).
 * client.ts's errorMiddleware throws ApiError on any non-2xx response
 * before this resolves, so `data` should always be defined here; the
 * explicit check below keeps that an assertion the type checker can see,
 * rather than a silent `!`.
 */
export function useMe(): UseQueryResult<Me> {
  return useQuery({
    queryKey: meQueryKey,
    queryFn: async () => {
      const { data } = await getApiClient().GET("/api/v1/auth/me");
      if (data === undefined) {
        throw new Error("GET /auth/me resolved with no data and no error");
      }
      return data;
    },
  });
}
