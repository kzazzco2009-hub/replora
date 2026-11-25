"use client";

import { isApiError } from "@/lib/api/problem";

type NextError = Error & { digest?: string };
type Lang = "en" | "ar";

// Placeholder i18n: next-intl replaces this at P9.3.
const strings: Record<
  Lang,
  { heading: string; body: string; retry: string; reference: string }
> = {
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

export function ErrorView({
  error,
  reset,
  lang = "en",
}: {
  error: NextError;
  reset: () => void;
  lang?: Lang;
}) {
  const t = strings[lang];
  const reference = isApiError(error)
    ? error.problem.correlation_id
    : error.digest;

  return (
    <div
      dir={lang === "ar" ? "rtl" : "ltr"}
      className="flex min-h-dvh flex-col items-start justify-center gap-4 ps-6 pe-6 text-start"
    >
      <h1 className="text-xl font-semibold">{t.heading}</h1>
      <p>{t.body}</p>
      <button
        type="button"
        onClick={reset}
        className="rounded border px-4 py-2"
      >
        {t.retry}
      </button>
      {reference ? (
        <p data-testid="error-reference" className="text-sm text-gray-500">
          {t.reference}: <span className="select-all">{reference}</span>
        </p>
      ) : null}
    </div>
  );
}
