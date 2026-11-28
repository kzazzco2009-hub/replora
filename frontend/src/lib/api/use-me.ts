import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { UseQueryResult } from "@tanstack/react-query";
import { getApiClient } from "./client";
import type { components } from "./schema";

export type Me = components["schemas"]["Me"];
export type UpdateMeRequest = components["schemas"]["UpdateMeRequest"];

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
    queryFn: async ({ signal }) => {
      const { data } = await getApiClient().GET("/api/v1/auth/me", { signal });
      if (data === undefined) {
        throw new Error("GET /auth/me resolved with no data and no error");
      }
      return data;
    },
  });
}

export async function updateMe(body: UpdateMeRequest) {
  const { data } = await getApiClient().PATCH("/api/v1/auth/me", { body });
  if (!data) throw new Error("Missing updated user response");
  return data;
}

export function useUpdateMe() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: updateMe,
    onSuccess: async (user) => {
      await client.cancelQueries({ queryKey: meQueryKey });
      client.setQueryData<Me>(meQueryKey, (me) =>
        me?.id === user.id ? { ...me, ...user } : me,
      );
    },
  });
}
