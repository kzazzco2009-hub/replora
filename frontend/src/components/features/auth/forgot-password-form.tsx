"use client";

import { useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
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

export function ForgotPasswordForm() {
  const t = useTranslations();
  const formRef = useRef<HTMLFormElement>(null);
  const alertRef = useRef<HTMLDivElement>(null);

  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      getApiClient().POST("/api/v1/auth/password/forgot", {
        body: { email },
      }),
    onSuccess: () => setSubmitted(true),
    onError: () => {
      requestAnimationFrame(() => {
        const invalid = formRef.current?.querySelector<HTMLElement>(
          '[aria-invalid="true"]',
        );
        (invalid ?? alertRef.current)?.focus();
      });
    },
  });

  // S-26: the backend always answers 202, used address or not — one neutral
  // success screen either way.
  if (submitted) {
    return (
      <AuthCard heading={t("auth.forgotPassword.checkEmailHeading")}>
        <p role="status" className="text-sm text-ink-muted">
          {t("auth.forgotPassword.checkEmailBody")}
        </p>
        <Link
          href="/sign-in"
          className="mt-4 inline-block text-sm font-medium text-petrol hover:underline"
        >
          {t("auth.forgotPassword.backToSignIn")}
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

  return (
    <AuthCard heading={t("auth.forgotPassword.heading")}>
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
          label={t("auth.forgotPassword.emailLabel")}
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={fieldMessage("email")}
        />
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
            ? t("auth.forgotPassword.submitPending")
            : t("auth.forgotPassword.submit")}
        </Button>
        <Link
          href="/sign-in"
          className="text-sm text-ink-muted hover:underline"
        >
          {t("auth.forgotPassword.backToSignIn")}
        </Link>
      </form>
    </AuthCard>
  );
}
