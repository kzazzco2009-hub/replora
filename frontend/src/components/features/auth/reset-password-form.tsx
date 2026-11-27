"use client";

import { useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link } from "@/i18n/routing";
import { getApiClient } from "@/lib/api/client";
import { mapProblem } from "@/lib/api/error-messages";
import { mapFieldErrors } from "@/lib/api/field-errors";
import { isApiError } from "@/lib/api/problem";
import { AuthCard } from "./auth-card";
import { FormAlert } from "./form-alert";

export function ResetPasswordForm() {
  const t = useTranslations();
  const token = useSearchParams().get("token");
  const formRef = useRef<HTMLFormElement>(null);
  const alertRef = useRef<HTMLDivElement>(null);

  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      getApiClient().POST("/api/v1/auth/password/reset", {
        body: { token: token ?? "", password },
      }),
    onError: () => {
      requestAnimationFrame(() => {
        const invalid = formRef.current?.querySelector<HTMLElement>(
          '[aria-invalid="true"]',
        );
        (invalid ?? alertRef.current)?.focus();
      });
    },
  });

  if (!token) {
    return (
      <AuthCard heading={t("auth.resetPassword.missingTokenHeading")}>
        <FormAlert title={t("auth.resetPassword.missingTokenBody")} />
        <Link
          href="/forgot-password"
          className="mt-4 inline-block text-sm font-medium text-petrol hover:underline"
        >
          {t("auth.resetPassword.toForgotPassword")}
        </Link>
      </AuthCard>
    );
  }

  if (mutation.isSuccess) {
    return (
      <AuthCard heading={t("auth.resetPassword.successHeading")}>
        <p role="status" className="text-sm text-ink-muted">
          {t("auth.resetPassword.successBody")}
        </p>
        <Link
          href="/sign-in"
          className="mt-4 inline-block text-sm font-medium text-petrol hover:underline"
        >
          {t("auth.resetPassword.toSignIn")}
        </Link>
      </AuthCard>
    );
  }

  const apiError = isApiError(mutation.error) ? mutation.error : null;
  const fieldErrors = apiError ? mapFieldErrors(apiError.problem) : null;
  const formAlert: {
    messageKey: string;
    params?: Record<string, unknown>;
    correlationId?: string | null;
  } | null =
    apiError && apiError.problem.code !== "VALIDATION_FAILED"
      ? mapProblem(apiError.problem)
      : (fieldErrors?.form[0] ?? null);

  function fieldMessage(name: string) {
    const field = fieldErrors?.fields[name];
    return field
      ? t(field.messageKey, field.params as Record<string, string | number>)
      : undefined;
  }

  const tokenInvalid = apiError?.problem.code === "TOKEN_INVALID";

  return (
    <AuthCard heading={t("auth.resetPassword.heading")}>
      <form
        ref={formRef}
        className="flex flex-col gap-4"
        onSubmit={(event) => {
          event.preventDefault();
          if (!mutation.isPending) mutation.mutate();
        }}
      >
        {formAlert ? (
          <div ref={alertRef} tabIndex={-1}>
            <FormAlert
              title={t(
                formAlert.messageKey,
                formAlert.params as Record<string, string | number> | undefined,
              )}
              correlationId={formAlert.correlationId ?? undefined}
              correlationIdLabel={t("errorView.reference")}
            />
          </div>
        ) : null}
        <Input
          label={t("auth.resetPassword.passwordLabel")}
          type="password"
          autoComplete="new-password"
          required
          minLength={12}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={fieldMessage("password")}
        />
        <p className="text-xs text-ink-muted">
          {t("auth.resetPassword.passwordHint")}
        </p>
        <Button
          type="submit"
          aria-busy={mutation.isPending}
          disabled={mutation.isPending}
        >
          {mutation.isPending ? (
            <Loader2
              aria-hidden="true"
              size={16}
              strokeWidth={1.75}
              className="animate-spin motion-reduce:animate-none"
            />
          ) : null}
          {mutation.isPending
            ? t("auth.resetPassword.submitPending")
            : t("auth.resetPassword.submit")}
        </Button>
        {tokenInvalid ? (
          <Link
            href="/forgot-password"
            className="text-sm text-ink-muted hover:underline"
          >
            {t("auth.resetPassword.toForgotPassword")}
          </Link>
        ) : null}
      </form>
    </AuthCard>
  );
}
