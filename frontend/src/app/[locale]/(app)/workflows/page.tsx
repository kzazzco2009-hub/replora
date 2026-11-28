"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, type TableColumn } from "@/components/ui/table";
import { mapProblem } from "@/lib/api/error-messages";
import { isApiError } from "@/lib/api/problem";
import { useMe } from "@/lib/api/use-me";
import { useWorkflows } from "@/lib/api/workflows";
import WorkflowsLoading from "./loading";

function WorkflowListError({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  const t = useTranslations();
  const key = isApiError(error)
    ? mapProblem(error.problem).messageKey
    : "errors.generic";
  return (
    <ErrorState
      title={t(key)}
      action={
        <Button variant="secondary" onClick={retry}>
          {t("runReview.retry")}
        </Button>
      }
    />
  );
}

function WorkflowsList({ workspaceId }: { workspaceId: string }) {
  const t = useTranslations("workflowList");
  const locale = useLocale();
  const [search, setSearch] = useState("");
  const [q, setQuery] = useState("");
  const trimmed = search.trim();
  useEffect(() => {
    if (trimmed === q) return;
    const timer = window.setTimeout(() => setQuery(trimmed), 300);
    return () => window.clearTimeout(timer);
  }, [trimmed, q]);

  const query = useWorkflows(workspaceId, q || undefined);
  const retry = query.isFetchNextPageError
    ? query.fetchNextPage
    : query.refetch;
  const dateFormat = new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
    numberingSystem: "latn",
  });
  const columns = [
    { key: "name", header: t("name"), rowHeader: true },
    { key: "version", header: t("version"), numeric: true },
    { key: "created", header: t("created"), numeric: true },
  ] satisfies TableColumn[];
  const rows = (query.data?.pages ?? []).flatMap(({ items }) =>
    items.map((workflow) => ({
      id: workflow.id,
      cells: {
        name: (
          <bdi className="whitespace-pre-wrap wrap-anywhere">
            {workflow.name}
          </bdi>
        ),
        version: workflow.latest_version,
        created: (
          <time dateTime={workflow.created_at}>
            {dateFormat.format(new Date(workflow.created_at))}
          </time>
        ),
      },
    })),
  );

  return (
    <>
      <label className="grid gap-1">
        {t("search")}
        <input
          type="search"
          className="rounded-control border border-line bg-surface px-3 [inline-size:min(100%,16rem)] [min-block-size:44px] focus-visible:outline-2 focus-visible:outline-focus-ring"
          maxLength={100}
          value={search}
          onChange={(event) => setSearch(event.currentTarget.value)}
        />
      </label>
      {(query.data || query.isPending) && (
        <Table
          caption={t("caption")}
          hideCaption
          columns={columns}
          rows={rows}
          loading={
            query.isPending && (
              <Skeleton
                variant="table-rows"
                columns={3}
                aria-label={t("loading")}
              />
            )
          }
          emptyState={<EmptyState title={t(q ? "noResults" : "empty")} />}
        />
      )}
      {query.isError && (
        <WorkflowListError error={query.error} retry={() => void retry()} />
      )}
      {!query.isError && query.hasNextPage && (
        <Button
          variant="secondary"
          className="self-start motion-reduce:transition-none"
          disabled={query.isFetching || trimmed !== q}
          onClick={() => void query.fetchNextPage()}
        >
          {t("more")}
        </Button>
      )}
    </>
  );
}

export default function WorkflowsPage() {
  const t = useTranslations();
  const me = useMe();
  const workspaceId = me.data?.memberships[0]?.id;
  if (me.isPending) return <WorkflowsLoading />;
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">{t("nav.workflows")}</h1>
      {workspaceId ? (
        <WorkflowsList workspaceId={workspaceId} />
      ) : me.isError ? (
        <WorkflowListError error={me.error} retry={() => void me.refetch()} />
      ) : (
        <EmptyState title={t("workflowList.noWorkspace")} />
      )}
    </div>
  );
}
