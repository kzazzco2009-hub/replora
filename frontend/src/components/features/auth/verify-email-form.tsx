"use client";

import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";
import { Link } from "@/i18n/routing";
import { getApiClient } from "@/lib/api/client";
import { mapProblem } from "@/lib/api/error-messages";
import { isApiError } from "@/lib/api/problem";
import { AuthCard } from "./auth-card";
import { FormAlert } from "./form-alert";

export function VerifyEmailForm() {
  const t = useTranslations();
  const token = useSearchParams().get("token");
  const fired = useRef(false);

  const mutation = useMutation({
    mutationFn: (verifyToken: string) =>
      getApiClient().POST("/api/v1/auth/verify-email", {
        body: { token: verifyToken },
      }),
  });

  useEffect(() => {
    if (fired.current || !token) return;
    fired.current = true;
    mutation.mutate(token);
  }, [token, mutation]);

  if (!token) {
    return (
      <AuthCard heading={t("auth.verifyEmail.missingTokenHeading")}>
        <FormAlert title={t("auth.verifyEmail.missingTokenBody")} />
        <Link
          href="/sign-up"
          className="mt-4 inline-block text-sm font-medium text-petrol hover:underline"
        >
          {t("auth.verifyEmail.toSignUp")}
        </Link>
      </AuthCard>
    );
  }

  if (mutation.isSuccess) {
    return (
      <AuthCard heading={t("auth.verifyEmail.successHeading")}>
        <p role="status" className="text-sm text-ink-muted">
          {t("auth.verifyEmail.successBody")}
        </p>
        <Link
          href="/sign-in"
          className="mt-4 inline-block text-sm font-medium text-petrol hover:underline"
        >
          {t("auth.verifyEmail.toSignIn")}
        </Link>
      </AuthCard>
    );
  }

  const apiError = isApiError(mutation.error) ? mutation.error : null;
  if (apiError) {
    const mapped = mapProblem(apiError.problem);
    return (
      <AuthCard heading={t("auth.verifyEmail.failureHeading")}>
        <FormAlert
          title={t(mapped.messageKey)}
          correlationId={mapped.correlationId ?? undefined}
          correlationIdLabel={t("errorView.reference")}
        />
        <div className="mt-4 flex flex-col gap-2 text-sm">
          <Link
            href="/sign-up"
            className="font-medium text-petrol hover:underline"
          >
            {t("auth.verifyEmail.toSignUp")}
          </Link>
          <Link href="/sign-in" className="text-ink-muted hover:underline">
            {t("auth.verifyEmail.toSignIn")}
          </Link>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard heading={t("auth.verifyEmail.loadingHeading")}>
      <p role="status" className="text-sm text-ink-muted">
        {t("auth.verifyEmail.loadingBody")}
      </p>
    </AuthCard>
  );
}
