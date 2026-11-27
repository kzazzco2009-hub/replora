"use client";

import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { RunReview } from "@/components/features/run-review/run-review";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useMe } from "@/lib/api/use-me";

export default function RunReviewPage() {
  const { runId } = useParams<{ runId: string }>();
  const t = useTranslations("runReview");
  const me = useMe();
  const wsId = me.data?.memberships[0]?.id;

  if (wsId) return <RunReview wsId={wsId} runId={runId} />;
  if (me.isPending)
    return <Skeleton variant="card" aria-label={t("loadingPlan")} />;
  return <ErrorState title={t("requestFailed")} />;
}
