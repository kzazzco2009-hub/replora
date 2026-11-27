"use client";

import { useTranslations } from "next-intl";
import { NewRunWizard } from "@/components/features/new-run/new-run-wizard";
import { Skeleton } from "@/components/ui/skeleton";
import { useMe } from "@/lib/api/use-me";

export default function NewRunPage() {
  const t = useTranslations("upload");
  const { data: me } = useMe();
  const wsId = me?.memberships[0]?.id;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-ink">{t("heading")}</h1>
      {wsId ? (
        <NewRunWizard wsId={wsId} />
      ) : (
        <Skeleton variant="card" aria-label={t("heading")} />
      )}
    </div>
  );
}
