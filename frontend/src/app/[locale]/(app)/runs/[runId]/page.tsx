"use client";

import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { RunProgress } from "@/components/features/run-progress/run-progress";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useMe } from "@/lib/api/use-me";
import { progressErrorKey } from "@/lib/api/runs";

export default function RunProgressPage() {
  const { runId } = useParams<{ runId: string }>();
  const t = useTranslations();
  const me = useMe();
  const wsId = me.data?.memberships[0]?.id;

  if (wsId) return <RunProgress wsId={wsId} runId={runId} />;
  if (me.isPending)
    return <Skeleton variant="card" aria-label={t("runProgress.loading")} />;
  return <ErrorState title={t(progressErrorKey(me.error))} />;
}
