"use client";

import { ErrorView } from "@/components/error-view";

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
        <ErrorView error={error} reset={reset} />
      </body>
    </html>
  );
}
