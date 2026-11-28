"use client";

import { useTranslations } from "next-intl";
import { Skeleton } from "@/components/ui/skeleton";

export default function WorkflowsLoading() {
  const t = useTranslations();

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">{t("nav.workflows")}</h1>
      <div aria-hidden="true" className="grid gap-1">
        <span>{t("workflowList.search")}</span>
        <div className="rounded-control bg-line [block-size:44px] [inline-size:min(100%,16rem)]" />
      </div>
      <div className="rounded-control border border-line p-3">
        <Skeleton
          variant="table-rows"
          columns={3}
          aria-label={t("workflowList.loading")}
        />
      </div>
    </div>
  );
}
