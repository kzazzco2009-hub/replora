"use client";

import { useTranslations } from "next-intl";
import { Skeleton } from "@/components/ui/skeleton";

export default function SettingsLoading() {
  const t = useTranslations("settings");
  return <Skeleton variant="text" count={4} aria-label={t("loading")} />;
}
