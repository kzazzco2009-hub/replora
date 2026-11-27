"use client";

import { useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
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

export function SignUpForm() {
  const t = useTranslations();
  const locale = useLocale() as "ar" | "en";
  const formRef = useRef<HTMLFormElement>(null);
  const alertRef = useRef<HTMLDivElement>(null);

  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const mutation = useMutation({
    mutationFn: () =>
      getApiClient().POST("/api/v1/auth/register", {
        body: { email, password, display_name: displayName, locale },
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

  // S-26: this is the one success state for every address, used or not.
  if (submitted) {
    return (
      <AuthCard heading={t("auth.signUp.checkEmailHeading")}>
        <p role="status" className="text-sm text-ink-muted">
          {t("auth.signUp.checkEmailBody")}
        </p>
        <Link
          href="/sign-in"
          className="mt-4 inline-block text-sm font-medium text-petrol hover:underline"
        >
          {t("auth.signUp.backToSignIn")}
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
    <AuthCard heading={t("auth.signUp.heading")}>
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
          label={t("auth.signUp.emailLabel")}
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={fieldMessage("email")}
        />
        <Input
          label={t("auth.signUp.displayNameLabel")}
          autoComplete="name"
          required
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          error={fieldMessage("display_name")}
        />
        <Input
          label={t("auth.signUp.passwordLabel")}
          type="password"
          autoComplete="new-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={fieldMessage("password")}
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
            ? t("auth.signUp.submitPending")
            : t("auth.signUp.submit")}
        </Button>
        <Link
          href="/sign-in"
          className="text-sm text-ink-muted hover:underline"
        >
          {t("auth.signUp.haveAccount")}
        </Link>
      </form>
    </AuthCard>
  );
}
