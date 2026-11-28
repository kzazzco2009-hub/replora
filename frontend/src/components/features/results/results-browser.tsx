"use client";

import {
  AlertTriangle,
  CheckCircle2,
  CircleMinus,
  Copy,
  ListFilter,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useFormatter, useLocale, useTranslations } from "next-intl";
import { useEffect, useId, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusChip } from "@/components/ui/status-chip";
import {
  Table,
  type TableColumn,
  type TableRowData,
} from "@/components/ui/table";
import { Tabs } from "@/components/ui/tabs";
import {
  isResultStatus,
  previewStatuses,
  resultsErrorKey,
  useOutputPreview,
  type OutputArtifact,
  type OutputLocation,
} from "@/lib/api/results";
import { RowLineage } from "./row-lineage";

const LIMIT = 100;
const filterStatuses = ["all", ...previewStatuses] as const;
const icons = {
  all: ListFilter,
  matched: CheckCircle2,
  value_diff: AlertTriangle,
  missing_left: CircleMinus,
  missing_right: CircleMinus,
  duplicate_key: Copy,
};
function changeQuery(values: Record<string, string | null>) {
  const url = new URL(window.location.href);
  for (const [key, value] of Object.entries(values)) {
    if (value === null) url.searchParams.delete(key);
    else url.searchParams.set(key, value);
  }
  if (url.href !== window.location.href)
    window.history.pushState(null, "", url);
}

function Preview({ location }: { location: OutputLocation }) {
  const t = useTranslations();
  const format = useFormatter();
  const dir = useLocale() === "ar" ? "rtl" : "ltr";
  const searchId = useId();
  const params = useSearchParams();
  const urlKey = params.toString();
  const [inspection, setInspection] = useState<{
    query: string;
    row: number;
  } | null>(null);
  const opener = useRef<HTMLButtonElement | null>(null);
  const q = params.get("q") ?? "";
  const status = params.get("status");
  const offsetValue = Number(params.get("offset") ?? 0);
  const offset =
    Number.isSafeInteger(offsetValue) && offsetValue >= 0 ? offsetValue : 0;
  const [draft, setDraft] = useState({ source: urlKey, value: q });
  if (draft.source !== urlKey) setDraft({ source: urlKey, value: q });
  const text = draft.source === urlKey ? draft.value : q;
  const trimmed = text.trim();
  useEffect(() => {
    if (trimmed === q) return;
    const timer = window.setTimeout(
      () => changeQuery({ q: trimmed || null, offset: null }),
      300,
    );
    return () => window.clearTimeout(timer);
  }, [trimmed, q, urlKey]);

  const query = useOutputPreview(location, {
    offset,
    limit: LIMIT,
    q: q || undefined,
    status: isResultStatus(status) ? status : undefined,
  });
  const page = query.data;
  const columns: TableColumn[] = [
    { key: "number", header: t("results.row"), numeric: true, rowHeader: true },
    ...(page?.columns ?? []).map((column, index) => ({
      key: `field-${index}`,
      header: <bdi>{column.name}</bdi>,
      numeric: ["integer", "decimal", "date"].includes(column.type),
    })),
    { key: "status", header: t("results.status") },
    { key: "actions", header: t("results.lineage.actions") },
  ];
  const rows: TableRowData[] = (page?.rows ?? []).map((row) => ({
    id: String(row.row),
    onClick: (event) => {
      if (event.target instanceof Element && !event.target.closest("button"))
        event.currentTarget.querySelector<HTMLButtonElement>("button")?.click();
    },
    cells: {
      number: row.row,
      actions: (
        <Button
          variant="secondary"
          className="min-w-11"
          aria-label={t("results.lineage.openRow", { row: String(row.row) })}
          onClick={(event) => {
            opener.current = event.currentTarget;
            setInspection({ query: urlKey, row: row.row });
          }}
        >
          {t("results.lineage.open")}
        </Button>
      ),
      ...Object.fromEntries(
        row.cells.map((cell, index) => [
          `field-${index}`,
          typeof cell === "boolean"
            ? t(cell ? "results.yes" : "results.no")
            : cell,
        ]),
      ),
      status: isResultStatus(row.status) ? (
        <StatusChip
          status={row.status}
          label={t(`results.statuses.${row.status}`)}
        />
      ) : (
        <span className="inline-flex items-center gap-1 text-ink-muted">
          <CircleMinus aria-hidden="true" size={14} />
          {t(
            row.status === null
              ? "results.statuses.none"
              : "results.statuses.unknown",
          )}
        </span>
      ),
    },
  }));
  const content = query.isPending ? (
    <Skeleton variant="card" aria-label={t("results.loading")} />
  ) : query.isError ? (
    <ErrorState
      title={t(resultsErrorKey(query.error))}
      action={
        <Button variant="secondary" onClick={() => void query.refetch()}>
          {t("runReview.retry")}
        </Button>
      }
    />
  ) : page === null ? (
    <EmptyState title={t("results.unavailable")} />
  ) : (
    <div className="space-y-3">
      <Table
        key={urlKey}
        caption={t("results.preview")}
        dir={dir}
        columns={columns}
        rows={rows}
        sticky
        emptyState={
          <EmptyState title={t("results.noRows")} headingLevel="h3" />
        }
      />
      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          disabled={!offset}
          onClick={() =>
            changeQuery({ offset: String(Math.max(0, offset - LIMIT)) })
          }
        >
          {t("results.previous")}
        </Button>
        <Button
          variant="secondary"
          disabled={!page || offset + LIMIT >= page.total}
          onClick={() => changeQuery({ offset: String(offset + LIMIT) })}
        >
          {t("results.next")}
        </Button>
      </div>
    </div>
  );
  return (
    <div className="min-w-0 space-y-3">
      <div className="flex flex-col items-start gap-1">
        <label htmlFor={searchId}>{t("results.search")}</label>
        <input
          id={searchId}
          type="search"
          value={text}
          onChange={(event) =>
            setDraft({ source: urlKey, value: event.target.value })
          }
          className="min-h-11 rounded-control border border-line px-3 focus-visible:outline-2 focus-visible:outline-focus-ring"
        />
      </div>
      <p role="status" aria-live="polite">
        {page
          ? t("results.count", {
              count: format.number(page.total, { numberingSystem: "latn" }),
            })
          : ""}
      </p>
      <Tabs
        dir={dir}
        label={t("results.filter")}
        value={isResultStatus(status) ? status : "all"}
        onValueChange={(value) =>
          changeQuery({ status: value === "all" ? null : value, offset: null })
        }
        tabs={filterStatuses.map((key) => {
          const Icon = icons[key];
          return {
            value: key,
            label: (
              <span className="inline-flex items-center gap-2">
                <Icon aria-hidden="true" size={16} />
                {t(key === "all" ? "results.all" : `results.statuses.${key}`)}
              </span>
            ),
            content,
          };
        })}
      />
      <RowLineage
        location={location}
        row={inspection?.query === urlKey ? inspection.row : null}
        onClose={() => setInspection(null)}
        restoreFocus={() => {
          const fallback = document.getElementById(searchId);
          (opener.current?.isConnected ? opener.current : fallback)?.focus();
          opener.current = null;
        }}
      />
    </div>
  );
}

export function ResultsBrowser({
  wsId,
  runId,
  files,
}: {
  wsId: string;
  runId: string;
  files: OutputArtifact[];
}) {
  const t = useTranslations("results");
  const id = useId();
  const selected = useSearchParams().get("artifact");
  const file = files.find(({ id }) => id === selected) ?? files[0];
  return (
    <section className="min-w-0 space-y-3">
      <label htmlFor={id} className="block font-semibold">
        {t("chooseOutput")}
      </label>
      <select
        id={id}
        value={file.id}
        className="min-h-11 max-w-full rounded-control border border-line bg-surface px-3"
        onChange={(event) =>
          changeQuery({
            artifact: event.target.value,
            offset: null,
            q: null,
            status: null,
          })
        }
      >
        {files.map((file) => (
          <option key={file.id} value={file.id}>
            {file.name}
          </option>
        ))}
      </select>
      <Preview key={file.id} location={{ wsId, runId, artifactId: file.id }} />
    </section>
  );
}
