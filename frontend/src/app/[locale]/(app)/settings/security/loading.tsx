"use client";

import { useTranslations } from "next-intl";
import { Skeleton } from "@/components/ui/skeleton";

export default function SecurityLoading() {
  const t = useTranslations("security");
  return <Skeleton variant="card" aria-label={t("loading")} />;
}
