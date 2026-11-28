"use client";

import {
  FileArchive,
  FileJson,
  FileQuestionMark,
  FileSpreadsheet,
} from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { formatBytes } from "@/components/features/upload/format-bytes";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, type TableColumn } from "@/components/ui/table";
import { mapProblem } from "@/lib/api/error-messages";
import { useFiles, type FileType } from "@/lib/api/files";
import { isApiError } from "@/lib/api/problem";
import { useMe } from "@/lib/api/use-me";
import FilesLoading from "./loading";

const typeIcons = { csv: FileSpreadsheet, json: FileJson, zip: FileArchive };
const types = ["csv", "json", "zip"] as const satisfies readonly FileType[];

function FilesError({ error, retry }: { error: unknown; retry: () => void }) {
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

function FilesList({ workspaceId }: { workspaceId: string }) {
  const t = useTranslations("fileList");
  const locale = useLocale();
  const [type, setType] = useState<FileType | "">("");
  const query = useFiles(workspaceId, type || undefined);
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
    { key: "type", header: t("type") },
    { key: "size", header: t("size"), numeric: true },
    { key: "created", header: t("created"), numeric: true },
  ] satisfies TableColumn[];

  const rows = (query.data?.pages ?? []).flatMap(({ items }) =>
    items.map((file) => {
      const type = file.detected_type;
      const known = type && Object.hasOwn(typeIcons, type);
      const Icon = known ? typeIcons[type] : FileQuestionMark;
      return {
        id: file.id,
        cells: {
          name: (
            <bdi className="whitespace-pre-wrap wrap-anywhere">
              {file.display_name}
            </bdi>
          ),
          type: (
            <span className="inline-flex items-center gap-2">
              <Icon aria-hidden="true" size={16} />
              {known ? type.toUpperCase() : t("unknown")}
            </span>
          ),
          size: formatBytes(file.size),
          created: (
            <time dateTime={file.created_at}>
              {dateFormat.format(new Date(file.created_at))}
            </time>
          ),
        },
      };
    }),
  );

  return (
    <>
      <label className="grid gap-1">
        {t("filter")}
        <select
          className="rounded-control border border-line bg-surface px-3 [inline-size:min(100%,16rem)] [min-block-size:44px] focus-visible:outline-2 focus-visible:outline-focus-ring"
          value={type}
          onChange={(event) =>
            setType(event.currentTarget.value as FileType | "")
          }
        >
          <option value="">{t("all")}</option>
          {types.map((value) => (
            <option key={value} value={value}>
              {value.toUpperCase()}
            </option>
          ))}
        </select>
      </label>
      {(query.data || query.isPending) && (
        <Table
          caption={t("caption")}
          hideCaption
          columns={columns}
          rows={rows}
          loading={
            query.isPending && (
              <Skeleton variant="table-rows" aria-label={t("loading")} />
            )
          }
          emptyState={<EmptyState title={t("empty")} />}
        />
      )}
      {query.isError && (
        <FilesError error={query.error} retry={() => void retry()} />
      )}
      {!query.isError && query.hasNextPage && (
        <Button
          variant="secondary"
          className="self-start motion-reduce:transition-none"
          disabled={query.isFetching}
          onClick={() => void query.fetchNextPage()}
        >
          {t("more")}
        </Button>
      )}
    </>
  );
}

export default function FilesPage() {
  const t = useTranslations();
  const me = useMe();
  const workspaceId = me.data?.memberships[0]?.id;
  if (me.isPending) return <FilesLoading />;
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">{t("nav.files")}</h1>
      {workspaceId ? (
        <FilesList workspaceId={workspaceId} />
      ) : me.isError ? (
        <FilesError error={me.error} retry={() => void me.refetch()} />
      ) : (
        <EmptyState title={t("fileList.noWorkspace")} />
      )}
    </div>
  );
}
