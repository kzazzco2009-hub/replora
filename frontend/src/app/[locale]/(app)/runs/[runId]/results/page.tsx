"use client";

import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { RunResults } from "@/components/features/results/run-results";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { resultsErrorKey } from "@/lib/api/results";
import { useMe } from "@/lib/api/use-me";

export default function ResultsPage() {
  const { runId } = useParams<{ runId: string }>();
  const t = useTranslations();
  const me = useMe();
  const wsId = me.data?.memberships[0]?.id;
  if (wsId) return <RunResults wsId={wsId} runId={runId} />;
  if (me.isPending)
    return <Skeleton variant="card" aria-label={t("results.loading")} />;
  return <ErrorState title={t(resultsErrorKey(me.error))} />;
}
