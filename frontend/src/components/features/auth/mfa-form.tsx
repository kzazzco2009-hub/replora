"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getApiClient } from "@/lib/api/client";
import { mapProblem } from "@/lib/api/error-messages";
import { mapFieldErrors } from "@/lib/api/field-errors";
import { isApiError } from "@/lib/api/problem";
import { meQueryKey } from "@/lib/api/use-me";
import { safeReturnTo } from "@/lib/safe-return-to";
import { AuthCard } from "./auth-card";
import { FormAlert } from "./form-alert";

function signInPath(
  locale: string,
  returnTo: string | null,
  expired?: boolean,
) {
  const params = new URLSearchParams();
  if (returnTo) params.set("returnTo", returnTo);
  if (expired) params.set("challengeExpired", "1");
  const query = params.toString();
  return `/${locale}/sign-in${query ? `?${query}` : ""}`;
}

export function MfaForm() {
  const t = useTranslations();
  const { locale } = useParams<{ locale: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const formRef = useRef<HTMLFormElement>(null);
  const alertRef = useRef<HTMLDivElement>(null);
  const returnTo = searchParams.get("returnTo");

  const [useRecovery, setUseRecovery] = useState(false);
  const [code, setCode] = useState("");
  const [recoveryCode, setRecoveryCode] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const body = useRecovery ? { recovery_code: recoveryCode } : { code };
      const { data } = await getApiClient().POST("/api/v1/auth/mfa/challenge", {
        body,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: meQueryKey });
      router.replace(safeReturnTo(returnTo, locale) ?? `/${locale}`);
    },
    onError: (error) => {
      if (isApiError(error) && error.problem.code === "MFA_CHALLENGE_INVALID") {
        router.replace(signInPath(locale, returnTo, true));
        return;
      }
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
    <AuthCard heading={t("auth.mfa.heading")}>
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
        {useRecovery ? (
          <Input
            label={t("auth.mfa.recoveryLabel")}
            autoComplete="off"
            required
            value={recoveryCode}
            onChange={(event) => setRecoveryCode(event.target.value)}
            error={fieldMessage("recovery_code")}
          />
        ) : (
          <Input
            label={t("auth.mfa.codeLabel")}
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            value={code}
            onChange={(event) => setCode(event.target.value)}
            error={fieldMessage("code")}
          />
        )}
        <button
          type="button"
          onClick={() => setUseRecovery((value) => !value)}
          className="min-h-11 self-start text-sm font-medium text-petrol underline-offset-2 hover:underline"
        >
          {useRecovery ? t("auth.mfa.useCode") : t("auth.mfa.useRecovery")}
        </button>
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
            ? t("auth.mfa.submitPending")
            : t("auth.mfa.submit")}
        </Button>
        <button
          type="button"
          onClick={() => router.replace(signInPath(locale, returnTo))}
          className="min-h-11 self-start text-sm font-medium text-ink-muted underline-offset-2 hover:underline"
        >
          {t("auth.mfa.back")}
        </button>
      </form>
    </AuthCard>
  );
}
