"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FormAlert } from "@/components/features/auth/form-alert";
import { getApiClient } from "@/lib/api/client";
import { mapProblem } from "@/lib/api/error-messages";
import { isApiError } from "@/lib/api/problem";
import { useMe } from "@/lib/api/use-me";

/** design.md §4: display name/email plus Sign out, behind the same native
 * `<details>` disclosure BottomTabBar's "More" overflow already uses. */
export function UserMenu() {
  const t = useTranslations();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: me } = useMe();

  const mutation = useMutation({
    mutationFn: () => getApiClient().POST("/api/v1/auth/logout"),
    onSuccess: signOut,
    onError: (error) => {
      // No session to revoke server-side; the client is signed out either way.
      if (isApiError(error) && error.problem.status === 401) signOut();
    },
  });

  function signOut() {
    queryClient.clear();
    router.replace(`/${locale}/sign-in`);
  }

  if (!me) return null;

  const error =
    isApiError(mutation.error) && mutation.error.problem.status !== 401
      ? mapProblem(mutation.error.problem)
      : null;

  return (
    <details className="relative">
      <summary className="flex min-h-11 min-w-11 cursor-pointer list-none items-center justify-center rounded-control px-2 text-sm font-medium text-ink [&::-webkit-details-marker]:hidden [&::marker]:hidden">
        <bdi>{me.display_name}</bdi>
      </summary>
      <div className="absolute end-0 z-50 mt-2 min-w-48 rounded-panel border border-line bg-surface-raised p-3 shadow-lg">
        <p className="text-sm text-ink-muted">
          <bdi>{me.email}</bdi>
        </p>
        {error ? (
          <div className="mt-2">
            <FormAlert
              title={t(error.messageKey)}
              correlationId={error.correlationId ?? undefined}
              correlationIdLabel={t("errorView.reference")}
            />
          </div>
        ) : null}
        <Button
          variant="secondary"
          className="mt-3 w-full"
          onClick={() => mutation.mutate()}
          aria-busy={mutation.isPending}
          disabled={mutation.isPending}
        >
          {mutation.isPending ? t("shell.signOutPending") : t("shell.signOut")}
        </Button>
      </div>
    </details>
  );
}
