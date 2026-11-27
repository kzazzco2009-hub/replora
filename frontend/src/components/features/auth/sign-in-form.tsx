"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link } from "@/i18n/routing";
import { getApiClient } from "@/lib/api/client";
import { mapProblem } from "@/lib/api/error-messages";
import { mapFieldErrors } from "@/lib/api/field-errors";
import { isApiError } from "@/lib/api/problem";
import { meQueryKey } from "@/lib/api/use-me";
import { safeReturnTo } from "@/lib/safe-return-to";
import { AuthCard } from "./auth-card";
import { FormAlert } from "./form-alert";
export function SignInForm() {
  const t = useTranslations();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const formRef = useRef<HTMLFormElement>(null);
  const alertRef = useRef<HTMLDivElement>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const { data } = await getApiClient().POST("/api/v1/auth/login", {
        body: { email, password },
      });
      return data;
    },
    onSuccess: (data) => {
      const returnTo = searchParams.get("returnTo");
      const query = returnTo ? `?returnTo=${encodeURIComponent(returnTo)}` : "";
      if (data && "mfa_required" in data) {
        router.replace(`/${locale}/mfa${query}`);
        return;
      }
      queryClient.invalidateQueries({ queryKey: meQueryKey });
      router.replace(safeReturnTo(returnTo, locale) ?? `/${locale}`);
    },
    onError: () => {
      requestAnimationFrame(() => {
        const invalid = formRef.current?.querySelector<HTMLElement>(
          '[aria-invalid="true"]',
        );
        (invalid ?? alertRef.current)?.focus();
      });
    },
  });

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
    <AuthCard heading={t("auth.signIn.heading")}>
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
          label={t("auth.signIn.emailLabel")}
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={fieldMessage("email")}
        />
        <Input
          label={t("auth.signIn.passwordLabel")}
          type="password"
          autoComplete="current-password"
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
            ? t("auth.signIn.submitPending")
            : t("auth.signIn.submit")}
        </Button>
        <div className="flex items-center justify-between gap-2 text-sm">
          <Link
            href="/sign-up"
            className="font-medium text-petrol hover:underline"
          >
            {t("auth.signIn.createAccount")}
          </Link>
          <Link
            href="/forgot-password"
            className="text-ink-muted hover:underline"
          >
            {t("auth.signIn.forgotPassword")}
          </Link>
        </div>
      </form>
    </AuthCard>
  );
}
