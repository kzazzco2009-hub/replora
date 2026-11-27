"use client";

import { AlertTriangle, Check, Circle, Clock } from "lucide-react";
import { useTranslations } from "next-intl";
import {
  IssueList,
  orderedNodes,
} from "@/components/features/run-review/run-plan";
import { operationTitleKey } from "@/components/features/run-review/operation-labels";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusChip } from "@/components/ui/status-chip";
import { runIsLive, useRunEvents, type RunEvent } from "@/lib/api/run-events";
import {
  progressErrorKey,
  useOperations,
  useRun,
  type Run,
  type RunIssue,
} from "@/lib/api/runs";
import { canCancelRun, RunActions, useCancelRun } from "./run-actions";

const stationIcons = {
  done: Check,
  active: Clock,
  waiting: Circle,
  warning: AlertTriangle,
};

function runStations(run: Run, events: RunEvent[]) {
  const nodes = orderedNodes(run.definition);
  const done = new Set<string>();
  const warnings = new Map<string, { nodeId?: string; issue: RunIssue }>();
  function add(issue: RunIssue, nodeId = issue.node_id ?? undefined) {
    warnings.set(
      JSON.stringify([nodeId, issue.code, issue.path, issue.params]),
      { nodeId, issue },
    );
  }
  for (const node of run.nodes) {
    if (node.finished_at && !node.error_code) done.add(node.node_id);
    node.warnings.forEach((issue) => add(issue, node.node_id));
  }
  run.review_issues.forEach((issue) => add(issue));
  let lastFinished = nodes.findLastIndex((node) => done.has(node.id));
  for (const event of events) {
    if (event.type === "warning")
      add(event.payload.issue, event.node_id ?? undefined);
    if (event.type === "node_finished") {
      done.add(event.node_id);
      const index = nodes.findIndex((node) => node.id === event.node_id);
      lastFinished = Math.max(lastFinished, index);
      event.payload.warnings.forEach((issue) => add(issue, event.node_id));
    }
  }
  return { nodes, done, warnings, activeId: nodes[lastFinished + 1]?.id };
}

function Pipeline({
  run,
  events,
  running,
}: {
  run: Run;
  events: RunEvent[];
  running: boolean;
}) {
  const t = useTranslations();
  const operations = useOperations();
  const { nodes, done, warnings, activeId } = runStations(run, events);
  const problemNodes = new Set(
    [...warnings.values()].map(({ nodeId }) => nodeId),
  );

  return (
    <section className="space-y-3">
      <h2 className="font-semibold">{t("runReview.pipeline")}</h2>
      {nodes.length ? (
        <ol
          aria-label={t("runReview.pipeline")}
          className="flex list-none flex-col gap-3 p-0 lg:flex-row lg:overflow-x-auto"
        >
          {nodes.map((node) => {
            const operation = operations.data?.find(
              (item) =>
                item.id === node.operation.id &&
                item.version === node.operation.version,
            );
            const key = operation && operationTitleKey(operation.title_key);
            const status = problemNodes.has(node.id)
              ? "warning"
              : done.has(node.id)
                ? "done"
                : running && node.id === activeId
                  ? "active"
                  : "waiting";
            const Icon = stationIcons[status];
            return (
              <li
                key={node.id}
                className={`relative flex min-w-0 items-start gap-3 before:absolute before:start-[17px] before:top-9 before:-bottom-3 before:border-s-2 last:before:hidden motion-safe:before:transition-colors lg:min-w-36 lg:flex-1 lg:flex-col lg:before:start-9 lg:before:-end-3 lg:before:top-[17px] lg:before:bottom-auto lg:before:border-s-0 lg:before:border-t-2 ${done.has(node.id) ? "before:border-petrol" : "before:border-line"}`}
              >
                <span
                  className={`flex size-9 shrink-0 items-center justify-center rounded-full border border-line motion-safe:transition-colors ${done.has(node.id) ? "bg-surface-raised text-petrol" : "text-ink-muted"}`}
                >
                  <Icon aria-hidden="true" size={18} />
                </span>
                <div className="min-w-0">
                  <h3 className="font-medium">
                    {key && t.has(key)
                      ? t(key)
                      : t("runReview.unknownOperation")}
                  </h3>
                  <bdi
                    dir="ltr"
                    className="block wrap-anywhere font-mono text-sm"
                  >
                    {node.id}
                  </bdi>
                  <p className="text-sm">
                    {t(`runProgress.station.${status}`)}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        <EmptyState title={t("runReview.emptyPlan")} headingLevel="h3" />
      )}
      <IssueList
        title={t("runReview.warnings")}
        issues={[...warnings.values()].map(({ issue }) => issue)}
      />
    </section>
  );
}

export function RunProgress({ wsId, runId }: { wsId: string; runId: string }) {
  const t = useTranslations();
  const query = useRun(wsId, runId);
  const run = query.data;
  const events = useRunEvents(wsId, runId, run?.state);
  const cancel = useCancelRun(
    wsId,
    runId,
    async () => (await query.refetch({ throwOnError: true })).data,
  );
  if (!run && query.isPending) {
    return <Skeleton variant="card" aria-label={t("runProgress.loading")} />;
  }
  if (!run) {
    return (
      <ErrorState
        title={t(progressErrorKey(query.error))}
        action={
          <Button variant="secondary" onClick={() => void query.refetch()}>
            {t("runReview.retry")}
          </Button>
        }
      />
    );
  }

  const eventState = events.data?.state;
  const beforeCancellation =
    run.state === "CANCEL_REQUESTED" &&
    (eventState === "QUEUED" || eventState === "RUNNING");
  const state =
    runIsLive(run.state) && !beforeCancellation
      ? (eventState ?? run.state)
      : run.state;
  const shown =
    cancel.isPending && canCancelRun(state) ? "CANCEL_REQUESTED" : state;
  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold">{t("runProgress.heading")}</h1>
        <div role="status" aria-live="polite" aria-atomic="true">
          <StatusChip status={shown} label={t(`runProgress.states.${shown}`)} />
        </div>
      </header>
      {events.isError && (
        <ErrorState title={t(progressErrorKey(events.error))} />
      )}
      <Pipeline
        run={run}
        events={events.data?.events ?? []}
        running={state === "RUNNING"}
      />
      <RunActions runId={runId} state={state} cancel={cancel} />
    </div>
  );
}
