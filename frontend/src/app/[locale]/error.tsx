"use client";

import { useLocale, useTranslations } from "next-intl";
import { ErrorView } from "@/components/error-view";
import { localeDirection } from "@/i18n/routing";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations("errorView");
  const locale = useLocale();

  return (
    <ErrorView
      error={error}
      reset={reset}
      dir={localeDirection(locale)}
      strings={{
        heading: t("heading"),
        body: t("body"),
        retry: t("retry"),
        reference: t("reference"),
      }}
    />
  );
}
