"use client";

import { ErrorView, type ErrorViewStrings } from "@/components/error-view";

// This boundary catches errors from outside the [locale] segment (including
// a failure in the locale layout itself), so it has no next-intl context
// and keeps its own minimal dict instead of useTranslations.
type Lang = "en" | "ar";

const STRINGS: Record<Lang, ErrorViewStrings> = {
  en: {
    heading: "Something went wrong",
    body: "Please try again. If this keeps happening, contact support with the reference below.",
    retry: "Try again",
    reference: "Reference",
  },
  ar: {
    heading: "حدث خطأ غير متوقع",
    body: "من فضلك أعد المحاولة. إذا تكرر الخطأ، تواصل مع الدعم وأرسل الرقم المرجعي أدناه.",
    retry: "إعادة المحاولة",
    reference: "الرقم المرجعي",
  },
};

export default function GlobalErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body>
        <ErrorView error={error} reset={reset} dir="ltr" strings={STRINGS.en} />
      </body>
    </html>
  );
}
