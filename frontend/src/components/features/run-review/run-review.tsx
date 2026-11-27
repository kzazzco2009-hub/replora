"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { isApiError } from "@/lib/api/problem";
import {
  approveRun,
  runErrorMessages,
  useOperations,
  useRun,
  type Run,
} from "@/lib/api/runs";
import { RunPlan } from "./run-plan";

export function RunReview({ wsId, runId }: { wsId: string; runId: string }) {
  const t = useTranslations();
  const locale = useLocale();
  const query = useRun(wsId, runId);
  const operations = useOperations();
  const [confirmHash, setConfirmHash] = useState<string | null>(null);
  const attempt = useRef<{ hash: string; key: string } | null>(null);
  const approve = useMutation({
    mutationFn: ({ hash, key }: { hash: string; key: string }) =>
      approveRun(runId, hash, { wsId, idempotencyKey: key }),
    onError: async (error) => {
      if (
        isApiError(error) &&
        error.problem.code === "INVALID_STATE_TRANSITION"
      ) {
        await query.refetch();
      }
    },
  });

  const run = approve.data ?? query.data;
  if (!run) {
    return query.isPending ? (
      <Skeleton variant="card" aria-label={t("runReview.loadingPlan")} />
    ) : (
      <ErrorState
        title={t(runErrorMessages(query.error)[0].messageKey)}
        action={
          <Button variant="secondary" onClick={() => void query.refetch()}>
            {t("runReview.retry")}
          </Button>
        }
      />
    );
  }

  const code = isApiError(approve.error)
    ? approve.error.problem.code
    : undefined;
  const reloadRequired =
    code === "PLAN_HASH_MISMATCH" || code === "INVALID_STATE_TRANSITION";
  const stateMessage: Partial<Record<Run["state"], string>> = {
    EXPIRED: "expired",
    QUEUED: "alreadyApproved",
    RUNNING: "alreadyApproved",
    CANCELLED: "cancelled",
    NEEDS_REVIEW: "needsReview",
  };

  const canApprove =
    run.state === "AWAITING_APPROVAL" &&
    !approve.isPending &&
    !reloadRequired &&
    (run.definition.nodes.length === 0 || operations.isSuccess);

  async function reload() {
    const result = await query.refetch();
    if (result.isSuccess) {
      attempt.current = null;
      approve.reset();
    }
  }

  function confirm(hash: string) {
    if (attempt.current?.hash !== hash) {
      attempt.current = { hash, key: crypto.randomUUID() };
    }
    setConfirmHash(null);
    approve.mutate(attempt.current);
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">{t("runReview.heading")}</h1>
      <RunPlan run={run} />
      <section className="flex flex-col items-start gap-3 border-t border-line pt-4">
        <p>
          {t("runReview.planHash")}{" "}
          <bdi className="font-mono">{run.plan_hash.slice(0, 8)}</bdi>
        </p>
        <div role="status" aria-live="polite">
          {approve.isPending && t("runReview.approving")}
          {approve.isSuccess && (
            <p>
              {t("runReview.approved")}{" "}
              <bdi className="font-mono">{run.id}</bdi>
            </p>
          )}
          {!approve.isSuccess &&
            run.state !== "AWAITING_APPROVAL" &&
            t(`runReview.${stateMessage[run.state] ?? "unavailable"}`)}
        </div>
        {approve.isSuccess && (
          <Link
            href={`/${locale}/runs/${encodeURIComponent(run.id)}`}
            className="inline-flex min-h-11 min-w-11 items-center rounded-control border border-line px-4 text-sm font-medium hover:bg-surface focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          >
            {t("runReview.openRun")}
          </Link>
        )}
        {run.state === "AWAITING_APPROVAL" && (
          <>
            {approve.isError && (
              <ul role="alert">
                {runErrorMessages(approve.error).map((message, index) => (
                  <li key={index}>
                    {t(
                      message.messageKey,
                      "params" in message
                        ? (message.params as Record<string, string | number>)
                        : undefined,
                    )}
                  </li>
                ))}
              </ul>
            )}
            {reloadRequired ? (
              <Button
                variant="secondary"
                disabled={query.isFetching}
                onClick={() => void reload()}
              >
                {t("runReview.reloadPlan")}
              </Button>
            ) : (
              <Button
                variant="stamp"
                disabled={!canApprove}
                onClick={() => setConfirmHash(run.plan_hash)}
              >
                {t("runReview.approve")}
              </Button>
            )}
          </>
        )}
      </section>
      <Dialog
        open={confirmHash !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmHash(null);
        }}
        title={t("runReview.confirmTitle")}
        closeLabel={t("runReview.close")}
      >
        <Button
          variant="stamp"
          disabled={confirmHash !== run.plan_hash || !canApprove}
          onClick={() => confirm(run.plan_hash)}
        >
          {t("runReview.approve")}
        </Button>
      </Dialog>
    </div>
  );
}
