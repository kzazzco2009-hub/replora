"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  runErrorMessages,
  useOperations,
  type Run,
  type RunIssue,
} from "@/lib/api/runs";
import { operationTitleKey } from "./operation-labels";

export function orderedNodes({ nodes, edges }: Run["definition"]) {
  const remaining = new Map(nodes.map((node) => [node.id, node]));
  const ordered: typeof nodes = [];
  while (remaining.size) {
    const next = [...remaining.values()].find(
      (node) =>
        !edges.some(
          (edge) =>
            edge.target.node_id === node.id &&
            remaining.has(edge.source.node_id),
        ),
    );
    if (!next) return [...ordered, ...remaining.values()];
    ordered.push(next);
    remaining.delete(next.id);
  }
  return ordered;
}

export function IssueList({
  title,
  issues,
}: {
  title: string;
  issues: RunIssue[];
}) {
  const t = useTranslations();
  if (!issues.length) return null;

  return (
    <section className="flex flex-col gap-2">
      <h3 className="font-medium">{title}</h3>
      <ul className="list-disc ps-5">
        {issues.map((issue, index) => {
          const key = `errors.validation.${issue.code}`;
          return (
            <li key={index}>
              {t.has(key)
                ? t(key, issue.params as Record<string, string | number>)
                : t("runReview.genericIssue")}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function RunPlan({ run }: { run: Run }) {
  const t = useTranslations();
  const operations = useOperations();
  const nodes = orderedNodes(run.definition);

  if (nodes.length && operations.isPending) {
    return <Skeleton variant="card" aria-label={t("runReview.loadingPlan")} />;
  }
  if (nodes.length && operations.isError) {
    return (
      <ErrorState
        title={t(runErrorMessages(operations.error)[0].messageKey)}
        action={
          <Button variant="secondary" onClick={() => void operations.refetch()}>
            {t("runReview.retry")}
          </Button>
        }
      />
    );
  }

  return (
    <section className="flex flex-col gap-4">
      <h2 className="font-semibold">{t("runReview.pipeline")}</h2>
      {nodes.length === 0 ? (
        <EmptyState title={t("runReview.emptyPlan")} headingLevel="h3" />
      ) : (
        <ol
          aria-label={t("runReview.pipeline")}
          className="m-0 flex list-none flex-col gap-3 overflow-x-auto p-0 lg:flex-row"
        >
          {nodes.map((node) => {
            const operation = operations.data?.find(
              (entry) =>
                entry.id === node.operation.id &&
                entry.version === node.operation.version,
            );
            const titleKey = operationTitleKey(node.operation.id);
            const title =
              titleKey && operation?.title_key === titleKey && t.has(titleKey)
                ? t(titleKey)
                : t("runReview.unknownOperation");
            const warnings =
              run.nodes.find((entry) => entry.node_id === node.id)?.warnings ??
              [];
            return (
              <li
                key={node.id}
                className="flex min-w-0 flex-col gap-3 border-s-2 border-line ps-3 lg:w-64 lg:shrink-0 lg:border-s-0 lg:border-t-2 lg:ps-0 lg:pt-3"
              >
                <article className="flex h-full flex-col gap-3 rounded-panel border border-line p-4">
                  <h3 className="font-medium">{title}</h3>
                  <dl className="flex flex-col gap-2 text-sm">
                    {(["inputs", "outputs"] as const).map((kind) => (
                      <div key={kind}>
                        <dt className="font-medium">
                          {t(`runReview.${kind}`)}
                        </dt>
                        <dd className="break-all">
                          {operation?.[kind].length
                            ? operation[kind].map((port) => (
                                <bdi key={port.name} className="block">
                                  {port.name}
                                </bdi>
                              ))
                            : t("runReview.noPorts")}
                        </dd>
                      </div>
                    ))}
                  </dl>
                  <IssueList
                    title={t("runReview.warnings")}
                    issues={warnings}
                  />
                </article>
              </li>
            );
          })}
        </ol>
      )}
      <IssueList title={t("runReview.issues")} issues={run.review_issues} />
      {run.state === "NEEDS_REVIEW" && (
        <p>{t("runReview.reviewAnswersLater")}</p>
      )}
    </section>
  );
}
