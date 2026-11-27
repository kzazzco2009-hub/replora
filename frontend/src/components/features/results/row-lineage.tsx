"use client";

import { useTranslations } from "next-intl";
import { operationTitleKey } from "@/components/features/run-review/operation-labels";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Sheet } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import {
  resultsErrorKey,
  useRowLineage,
  type OutputLocation,
} from "@/lib/api/results";

export function RowLineage({
  location,
  row,
  onClose,
  restoreFocus,
}: {
  location: OutputLocation;
  row: number | null;
  onClose: () => void;
  restoreFocus: () => void;
}) {
  const t = useTranslations();
  const query = useRowLineage(location, row);
  const sources = query.data?.sources ?? [];
  const operations = query.data?.operations ?? [];
  return (
    <Sheet
      open={row !== null}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
      title={t("results.lineage.title")}
      closeLabel={t("runReview.close")}
      onCloseAutoFocus={(event) => {
        event.preventDefault();
        restoreFocus();
      }}
    >
      <p>
        {t("results.row")} <bdi dir="ltr">{row}</bdi>
      </p>
      {query.isPending ? (
        <Skeleton variant="card" aria-label={t("results.lineage.loading")} />
      ) : query.isError ? (
        <ErrorState
          headingLevel="h3"
          title={t(resultsErrorKey(query.error))}
          action={
            <Button variant="secondary" onClick={() => void query.refetch()}>
              {t("runReview.retry")}
            </Button>
          }
        />
      ) : sources.length + operations.length === 0 ? (
        <EmptyState title={t("results.lineage.empty")} headingLevel="h3" />
      ) : (
        <>
          {sources.length > 0 && (
            <section className="space-y-2">
              <h3 className="font-semibold">{t("results.lineage.sources")}</h3>
              <ul className="space-y-2">
                {sources.map((source, index) => (
                  <li
                    key={index}
                    className="space-y-1 rounded-control border border-line p-3 wrap-anywhere"
                  >
                    <p>
                      {t("results.lineage.file")}{" "}
                      <bdi dir="ltr">
                        {typeof source?.file_id === "string"
                          ? source.file_id
                          : "—"}
                      </bdi>
                    </p>
                    {typeof source?.member_path === "string" && (
                      <p>
                        <bdi>{source.member_path}</bdi>
                      </p>
                    )}
                    {typeof source?.row === "number" && (
                      <p>
                        {t("results.row")} <bdi dir="ltr">{source.row}</bdi>
                      </p>
                    )}
                    {typeof source?.page === "number" && (
                      <p>
                        {t("results.lineage.page")}{" "}
                        <bdi dir="ltr">{source.page}</bdi>
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}
          {operations.length > 0 && (
            <section className="space-y-2">
              <h3 className="font-semibold">
                {t("results.lineage.operations")}
              </h3>
              <ul className="list-disc space-y-2 ps-5 wrap-anywhere">
                {operations.map((operation, index) => {
                  const id =
                    typeof operation?.id === "string" ? operation.id : "";
                  const key = operationTitleKey(id);
                  return (
                    <li key={index}>
                      {key && t.has(key)
                        ? t(key)
                        : t("runReview.unknownOperation")}
                      {!key && id && (
                        <>
                          {" "}
                          <bdi dir="ltr">{id}</bdi>
                        </>
                      )}
                      {typeof operation?.version === "number" && (
                        <>
                          {" · "}
                          {t("results.lineage.version")}{" "}
                          <bdi dir="ltr">{operation.version}</bdi>
                        </>
                      )}
                    </li>
                  );
                })}
              </ul>
            </section>
          )}
        </>
      )}
    </Sheet>
  );
}
