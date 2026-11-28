"use client";

import {
  skipToken,
  useQuery,
  type UseQueryResult,
} from "@tanstack/react-query";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusChip } from "@/components/ui/status-chip";
import { listRuns } from "@/lib/api/runs";
import { useMe } from "@/lib/api/use-me";
import { listWorkflows } from "@/lib/api/workflows";

const limit = 5;
const linkClass =
  "inline-flex items-center rounded-control [min-block-size:44px] [min-inline-size:44px] focus-visible:outline-2 focus-visible:outline-focus-ring";

function HomeList({
  id,
  title,
  viewAll,
  loading,
  empty,
  error,
  source,
  items,
}: {
  id: "runs" | "workflows";
  title: string;
  viewAll: string;
  loading: string;
  empty: string;
  error: string;
  source: Pick<UseQueryResult, "status" | "isFetching" | "refetch">;
  items?: ReactNode[];
}) {
  const locale = useLocale();
  const t = useTranslations();
  const headingId = `home-${id}`;
  return (
    <section
      aria-labelledby={headingId}
      className="grid content-start gap-3 rounded-control border border-line p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-x-4">
        <h2 id={headingId} className="text-lg font-semibold">
          {title}
        </h2>
        <Link
          href={`/${locale}/${id}`}
          className={`${linkClass} text-sm text-petrol underline`}
        >
          {viewAll}
        </Link>
      </div>
      {source.status === "pending" ? (
        <Skeleton variant="text" aria-label={loading} />
      ) : source.status === "error" ? (
        <ErrorState
          headingLevel="h3"
          title={error}
          action={
            <Button
              variant="secondary"
              className="motion-reduce:transition-none"
              disabled={source.isFetching}
              onClick={() => void source.refetch()}
            >
              {t("runReview.retry")}
            </Button>
          }
        />
      ) : items?.length ? (
        <ul className="grid gap-2">{items}</ul>
      ) : (
        <EmptyState headingLevel="h3" title={empty} />
      )}
    </section>
  );
}

export default function Home() {
  const t = useTranslations();
  const locale = useLocale();
  const me = useMe();
  const workspaceId = me.data?.memberships[0]?.id;
  const runs = useQuery({
    queryKey: ["runs", workspaceId, { limit }],
    queryFn: workspaceId
      ? ({ signal }) => listRuns({ workspaceId, limit }, signal)
      : skipToken,
  });
  const workflows = useQuery({
    queryKey: ["workflows", workspaceId, { limit }],
    queryFn: workspaceId
      ? ({ signal }) => listWorkflows({ workspaceId, limit }, signal)
      : skipToken,
  });
  const dateFormat = new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
    numberingSystem: "latn",
  });

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">{t("home.title")}</h1>
        <Link
          href={`/${locale}/new-run`}
          className={`${linkClass} bg-petrol px-4 text-sm font-medium text-petrol-contrast hover:opacity-90`}
        >
          {t("home.newReconciliation")}
        </Link>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <HomeList
          id="runs"
          title={t("home.recentRuns")}
          viewAll={t("home.viewAllRuns")}
          loading={t("runHistory.loading")}
          empty={t(workspaceId ? "runHistory.empty" : "runHistory.noWorkspace")}
          error={t("home.runsError")}
          source={workspaceId ? runs : me}
          items={runs.data?.items.map((run) => {
            const needsReview =
              run.state === "AWAITING_APPROVAL" || run.state === "NEEDS_REVIEW";
            const href = `/${locale}/runs/${encodeURIComponent(run.id)}${needsReview ? "/review" : ""}`;
            return (
              <li
                key={run.id}
                className="flex flex-wrap items-center justify-between gap-x-3 rounded-control bg-surface px-3 py-2"
              >
                <div className="grid content-start [min-inline-size:0]">
                  <Link
                    href={href}
                    className={`${linkClass} justify-self-start text-petrol underline`}
                  >
                    <bdi
                      dir="ltr"
                      className="whitespace-pre-wrap wrap-anywhere"
                    >
                      {run.title}
                    </bdi>
                  </Link>
                  <bdi dir="ltr" className="text-sm text-ink-muted">
                    <time dateTime={run.created_at}>
                      {dateFormat.format(new Date(run.created_at))}
                    </time>
                  </bdi>
                </div>
                <StatusChip
                  status={run.state}
                  label={t(`runProgress.states.${run.state}`)}
                />
              </li>
            );
          })}
        />
        <HomeList
          id="workflows"
          title={t("workflowList.caption")}
          viewAll={t("home.viewAllWorkflows")}
          loading={t("workflowList.loading")}
          empty={t(
            workspaceId ? "workflowList.empty" : "workflowList.noWorkspace",
          )}
          error={t("home.workflowsError")}
          source={workspaceId ? workflows : me}
          items={workflows.data?.items.map((workflow) => (
            <li
              key={workflow.id}
              className="rounded-control bg-surface px-3 py-2"
            >
              <bdi className="whitespace-pre-wrap wrap-anywhere">
                {workflow.name}
              </bdi>
            </li>
          ))}
        />
      </div>
    </div>
  );
}
