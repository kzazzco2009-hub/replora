"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { isApiError } from "@/lib/api/problem";
import {
  cancelRun,
  progressErrorKey,
  runQueryKey,
  type Run,
} from "@/lib/api/runs";

const terminal = {
  SUCCEEDED: "succeeded",
  PARTIAL: "partial",
  FAILED: "failed",
  CANCELLED: "cancelled",
  EXPIRED: "expired",
} as const;

export function canCancelRun(state: Run["state"]) {
  return (
    state === "AWAITING_APPROVAL" ||
    state === "QUEUED" ||
    state === "RUNNING" ||
    state === "NEEDS_REVIEW"
  );
}

export function useCancelRun(
  wsId: string,
  runId: string,
  refresh: () => Promise<Run | undefined>,
) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      try {
        return { run: await cancelRun(wsId, runId), conflict: false };
      } catch (error) {
        if (
          !isApiError(error) ||
          error.problem.status !== 409 ||
          error.problem.code !== "INVALID_STATE_TRANSITION"
        )
          throw error;
        const latest = await refresh();
        if (!latest) throw error;
        return { run: latest, conflict: true };
      }
    },
    onSuccess: async ({ run }) => {
      const queryKey = runQueryKey(wsId, runId);
      await client.cancelQueries({ queryKey });
      client.setQueryData(queryKey, run);
    },
  });
}

const linkClass =
  "inline-flex min-h-11 min-w-11 items-center rounded-control px-3 font-medium text-petrol underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring";

export function RunActions({
  runId,
  state,
  cancel,
}: {
  runId: string;
  state: Run["state"];
  cancel: ReturnType<typeof useCancelRun>;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const [open, setOpen] = useState(false);
  const outcome = Object.hasOwn(terminal, state)
    ? terminal[state as keyof typeof terminal]
    : undefined;
  const conflictState = cancel.data?.conflict
    ? cancel.data.run.state
    : undefined;
  const conflictMessage =
    conflictState &&
    (conflictState === "CANCEL_REQUESTED" || conflictState === "CANCELLED"
      ? t(`runProgress.states.${conflictState}`)
      : Object.hasOwn(terminal, conflictState)
        ? t("runProgress.alreadyFinished")
        : t("errors.problem.INVALID_STATE_TRANSITION"));
  if (
    !outcome &&
    !conflictMessage &&
    !cancel.isError &&
    !cancel.isPending &&
    !canCancelRun(state)
  )
    return null;

  return (
    <section className="space-y-3 border-t border-line pt-4">
      {conflictMessage && <p role="alert">{conflictMessage}</p>}
      {cancel.isError && (
        <p role="alert">{t(progressErrorKey(cancel.error))}</p>
      )}
      {outcome && (
        <>
          <p>{t(`runProgress.outcome.${outcome}`)}</p>
          <div className="flex flex-wrap gap-2">
            {(state === "SUCCEEDED" || state === "PARTIAL") && (
              <Button variant="secondary" disabled>
                {t("runProgress.viewResults")}
              </Button>
            )}
            <Link className={linkClass} href={`/${locale}/new-run`}>
              {t("nav.newRun")}
            </Link>
          </div>
        </>
      )}
      {state === "NEEDS_REVIEW" && (
        <>
          <p>{t("runReview.reviewAnswersLater")}</p>
          <Link
            className={linkClass}
            href={`/${locale}/runs/${encodeURIComponent(runId)}/review`}
          >
            {t("runReview.heading")}
          </Link>
        </>
      )}
      {(canCancelRun(state) || cancel.isPending) && (
        <Button
          variant="secondary"
          disabled={cancel.isPending}
          onClick={() => setOpen(true)}
        >
          {t("runProgress.cancel")}
        </Button>
      )}
      <Dialog
        open={open && canCancelRun(state)}
        onOpenChange={setOpen}
        title={t("runProgress.confirmCancel")}
        closeLabel={t("runReview.close")}
      >
        <Button
          variant="secondary"
          disabled={cancel.isPending}
          onClick={() => {
            setOpen(false);
            cancel.mutate();
          }}
        >
          {t("runProgress.cancel")}
        </Button>
      </Dialog>
    </section>
  );
}
