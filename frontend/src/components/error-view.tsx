"use client";

import { isApiError } from "@/lib/api/problem";

type NextError = Error & { digest?: string };

export interface ErrorViewStrings {
  heading: string;
  body: string;
  retry: string;
  reference: string;
}

export function ErrorView({
  error,
  reset,
  dir = "ltr",
  strings,
}: {
  error: NextError;
  reset: () => void;
  dir?: "ltr" | "rtl";
  strings: ErrorViewStrings;
}) {
  const reference = isApiError(error)
    ? error.problem.correlation_id
    : error.digest;

  return (
    <div
      dir={dir}
      className="flex min-h-dvh flex-col items-start justify-center gap-4 ps-6 pe-6 text-start"
    >
      <h1 className="text-xl font-semibold">{strings.heading}</h1>
      <p>{strings.body}</p>
      <button
        type="button"
        onClick={reset}
        className="rounded border px-4 py-2"
      >
        {strings.retry}
      </button>
      {reference ? (
        <p data-testid="error-reference" className="text-sm text-gray-500">
          {strings.reference}:{" "}
          <bdi dir="ltr" className="select-all">
            {reference}
          </bdi>
        </p>
      ) : null}
    </div>
  );
}
