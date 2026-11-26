import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { getApiClient } from "./client";
import type { components } from "./schema";

export type Me = components["schemas"]["Me"];

/**
 * The current user and their workspace memberships (GET /auth/me).
 * client.ts's errorMiddleware throws ApiError on any non-2xx response
 * before this resolves, so `data` is always defined here.
 */
export function useMe(): UseQueryResult<Me> {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await getApiClient().GET("/api/v1/auth/me");
      return data!;
    },
  });
}
