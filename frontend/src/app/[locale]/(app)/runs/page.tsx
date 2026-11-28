"use client";

import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusChip } from "@/components/ui/status-chip";
import { Table, type TableColumn } from "@/components/ui/table";
import { runErrorMessages, useRuns, type Run } from "@/lib/api/runs";
import { useMe } from "@/lib/api/use-me";
import RunsLoading from "./loading";

type RunState = Run["state"];
const states = [
  "DRAFT",
  "VALIDATED",
  "AWAITING_APPROVAL",
  "QUEUED",
  "RUNNING",
  "NEEDS_REVIEW",
  "SUCCEEDED",
  "PARTIAL",
  "FAILED",
  "CANCEL_REQUESTED",
  "CANCELLED",
  "EXPIRED",
] as const satisfies readonly RunState[];

function HistoryError({ error, retry }: { error: unknown; retry: () => void }) {
  const t = useTranslations();
  return (
    <ErrorState
      title={t(runErrorMessages(error)[0].messageKey)}
      action={
        <Button variant="secondary" onClick={retry}>
          {t("runReview.retry")}
        </Button>
      }
    />
  );
}

function RunsHistory({ workspaceId }: { workspaceId: string }) {
  const t = useTranslations();
  const locale = useLocale();
  const [state, setState] = useState<RunState | "">("");
  const query = useRuns(workspaceId, state || undefined);
  const retry = query.isFetchNextPageError
    ? query.fetchNextPage
    : query.refetch;
  const dateFormat = new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
    numberingSystem: "latn",
  });
  function dateCell(value: string) {
    return (
      <bdi dir="ltr">
        <time dateTime={value}>{dateFormat.format(new Date(value))}</time>
      </bdi>
    );
  }

  const columns = [
    { key: "run", header: t("runHistory.run"), rowHeader: true },
    { key: "status", header: t("runHistory.status") },
    { key: "created", header: t("runHistory.created"), align: "end" },
    { key: "finished", header: t("runHistory.finished"), align: "end" },
  ] satisfies TableColumn[];

  const rows = (query.data?.pages ?? []).flatMap(({ items }) =>
    items.map((run) => {
      const needsReview =
        run.state === "AWAITING_APPROVAL" || run.state === "NEEDS_REVIEW";
      const href = `/${locale}/runs/${encodeURIComponent(run.id)}${needsReview ? "/review" : ""}`;
      return {
        id: run.id,
        cells: {
          run: (
            <Link
              href={href}
              className="flex flex-col items-start justify-center rounded-control text-petrol underline [min-block-size:44px] focus-visible:outline-2 focus-visible:outline-focus-ring"
            >
              <bdi dir="ltr" className="whitespace-pre-wrap">
                {run.title}
              </bdi>
              <bdi dir="ltr" className="font-mono text-xs">
                {run.id}
              </bdi>
            </Link>
          ),
          status: (
            <StatusChip
              status={run.state}
              label={t(`runProgress.states.${run.state}`)}
            />
          ),
          created: dateCell(run.created_at),
          finished: run.finished_at
            ? dateCell(run.finished_at)
            : t("runHistory.unfinished"),
        },
      };
    }),
  );

  return (
    <>
      <label className="grid gap-1">
        {t("runHistory.filter")}
        <select
          className="rounded-control border border-line bg-surface px-3 [inline-size:min(100%,16rem)] [min-block-size:44px] focus-visible:outline-2 focus-visible:outline-focus-ring"
          value={state}
          onChange={(event) =>
            setState(event.currentTarget.value as RunState | "")
          }
        >
          <option value="">{t("runHistory.all")}</option>
          {states.map((value) => (
            <option key={value} value={value}>
              {t(`runProgress.states.${value}`)}
            </option>
          ))}
        </select>
      </label>
      {(query.data || query.isPending) && (
        <Table
          caption={t("runHistory.heading")}
          hideCaption
          columns={columns}
          rows={rows}
          loading={
            query.isPending && (
              <Skeleton
                variant="table-rows"
                aria-label={t("runHistory.loading")}
              />
            )
          }
          emptyState={<EmptyState title={t("runHistory.empty")} />}
        />
      )}
      {query.isError && (
        <HistoryError error={query.error} retry={() => void retry()} />
      )}
      {!query.isError && query.hasNextPage && (
        <Button
          variant="secondary"
          className="self-start motion-reduce:transition-none"
          disabled={query.isFetching}
          onClick={() => void query.fetchNextPage()}
        >
          {t("runHistory.more")}
        </Button>
      )}
    </>
  );
}

export default function RunsPage() {
  const t = useTranslations("runHistory");
  const me = useMe();
  const workspaceId = me.data?.memberships[0]?.id;
  if (me.isPending) return <RunsLoading />;
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">{t("heading")}</h1>
      {workspaceId ? (
        <RunsHistory workspaceId={workspaceId} />
      ) : me.isError ? (
        <HistoryError error={me.error} retry={() => void me.refetch()} />
      ) : (
        <EmptyState title={t("noWorkspace")} />
      )}
    </div>
  );
}
