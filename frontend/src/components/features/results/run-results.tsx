"use client";

import { useFormatter, useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusChip } from "@/components/ui/status-chip";
import { resultStatuses, resultsErrorKey, useOutputs } from "@/lib/api/results";
import { useRun, type Run } from "@/lib/api/runs";
import { DownloadOutput } from "./download-output";

function OutputFiles({ wsId, runId }: { wsId: string; runId: string }) {
  const t = useTranslations();
  const format = useFormatter();
  const query = useOutputs({ wsId, runId });
  if (query.isPending)
    return <Skeleton variant="card" aria-label={t("results.loading")} />;
  if (query.isError)
    return (
      <ErrorState
        title={t(resultsErrorKey(query.error))}
        action={
          <Button variant="secondary" onClick={() => void query.refetch()}>
            {t("runReview.retry")}
          </Button>
        }
      />
    );
  if (query.data.length === 0)
    return <EmptyState title={t("results.noFiles")} />;
  return (
    <section className="min-w-0 space-y-3">
      <h2 className="text-lg font-semibold">{t("results.files")}</h2>
      <ul className="divide-y divide-line">
        {query.data.map((file) => (
          <li
            className="flex flex-wrap items-center justify-between gap-3 py-3"
            key={file.id}
          >
            <div className="min-w-0 wrap-anywhere">
              <bdi className="font-medium">{file.name}</bdi>
              <p className="text-sm text-ink-muted">
                <bdi>
                  {format.number(file.size, {
                    style: "unit",
                    unit: "byte",
                    numberingSystem: "latn",
                  })}
                </bdi>
              </p>
            </div>
            <DownloadOutput
              location={{ wsId, runId, artifactId: file.id }}
              filename={file.name}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}

function StatusSummary({ summary }: { summary: NonNullable<Run["summary"]> }) {
  const t = useTranslations("results");
  const format = useFormatter();
  return (
    <section className="space-y-2">
      <h2 className="text-lg font-semibold">{t("summary")}</h2>
      <dl className="flex flex-wrap gap-3">
        {resultStatuses.map((status) => (
          <div
            key={status}
            className="flex items-center gap-2 rounded-control border border-line p-2"
          >
            <dt>
              <StatusChip status={status} label={t(`statuses.${status}`)} />
            </dt>
            <dd>
              <bdi dir="ltr">
                {format.number(summary[status], { numberingSystem: "latn" })}
              </bdi>
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function RunResults({ wsId, runId }: { wsId: string; runId: string }) {
  const t = useTranslations();
  const run = useRun(wsId, runId);
  if (run.isPending)
    return <Skeleton variant="card" aria-label={t("results.loading")} />;
  if (run.isError)
    return (
      <ErrorState
        title={t(resultsErrorKey(run.error))}
        action={
          <Button variant="secondary" onClick={() => void run.refetch()}>
            {t("runReview.retry")}
          </Button>
        }
      />
    );
  const ready = run.data.state === "SUCCEEDED" || run.data.state === "PARTIAL";
  return (
    <div className="flex min-w-0 flex-col gap-6">
      <h1 className="text-xl font-semibold">{t("results.heading")}</h1>
      {run.data.state === "PARTIAL" && (
        <p>{t("runProgress.outcome.partial")}</p>
      )}
      {ready ? (
        <>
          {run.data.summary && <StatusSummary summary={run.data.summary} />}
          <OutputFiles wsId={wsId} runId={runId} />
        </>
      ) : (
        <EmptyState title={t("results.notReady")} />
      )}
    </div>
  );
}
