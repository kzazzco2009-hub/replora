"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { FormAlert } from "@/components/features/auth/form-alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRouter } from "@/i18n/routing";
import { mapProblem } from "@/lib/api/error-messages";
import { confirmMfaEnrollment, disableMfa, enrollMfa } from "@/lib/api/mfa";
import { isApiError } from "@/lib/api/problem";
import { meQueryKey, useMe } from "@/lib/api/use-me";
import SecurityLoading from "./loading";

const unauthenticated = "errors.problem.UNAUTHENTICATED";

function errorKey(error: unknown) {
  if (!isApiError(error)) return "errors.generic";
  if (error.problem.status === 401) return unauthenticated;
  const { messageKey } = mapProblem(error.problem);
  return messageKey === "errors.problem.MFA_CODE_INVALID"
    ? "security.invalidCode"
    : messageKey;
}

export default function SecurityPage() {
  const t = useTranslations();
  const me = useMe();
  const client = useQueryClient();
  const router = useRouter();
  const [setup, setSetup] = useState<{
    uri: string;
    secret: string;
    codes: string[];
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [actionError, setActionError] = useState<string>();
  const error = me.error ? errorKey(me.error) : actionError;

  useEffect(() => {
    if (error === unauthenticated) {
      client.clear();
      router.replace("/sign-in");
    }
  }, [client, error, router]);

  async function perform(action: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setActionError(undefined);
    setCopied(false);
    try {
      await action();
    } catch (error) {
      setActionError(errorKey(error));
    } finally {
      setBusy(false);
    }
  }

  if (me.isPending || error === unauthenticated) return <SecurityLoading />;
  const enabled = me.data?.mfa_enabled;

  return (
    <div className="grid justify-items-start gap-4 [max-inline-size:36rem]">
      <h1 className="text-xl font-semibold">{t("security.heading")}</h1>
      {error && <FormAlert title={t(error)} />}
      {me.isError ? (
        <Button
          variant="secondary"
          onClick={() => void me.refetch()}
          disabled={me.isFetching}
        >
          {t("runReview.retry")}
        </Button>
      ) : (
        <>
          <p role="status">
            {t(enabled ? "security.enabled" : "security.disabled")}
          </p>
          {!enabled && !setup && (
            <Button
              disabled={busy}
              onClick={() =>
                void perform(async () => {
                  const { otpauth_uri, recovery_codes } = await enrollMfa();
                  const uri = new URL(otpauth_uri);
                  const secret = uri.searchParams.get("secret");
                  if (uri.protocol !== "otpauth:" || !secret)
                    throw new Error("Invalid enrollment URI");
                  setSetup({ uri: otpauth_uri, secret, codes: recovery_codes });
                })
              }
            >
              {t("security.enable")}
            </Button>
          )}
          {!enabled && setup && (
            <section className="grid justify-items-start gap-2">
              <h2 className="font-semibold">{t("security.setupKey")}</h2>
              <bdi dir="ltr" className="font-mono wrap-anywhere">
                {setup.secret}
              </bdi>
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() =>
                  void perform(async () => {
                    await navigator.clipboard.writeText(setup.secret);
                    setCopied(true);
                  })
                }
              >
                {t("security.copyKey")}
              </Button>
              <a
                href={setup.uri}
                className="inline-flex items-center rounded-control text-petrol underline [min-block-size:44px] [min-inline-size:44px] focus-visible:outline-2 focus-visible:outline-focus-ring"
              >
                {t("security.openApp")}
              </a>
              <h2 className="font-semibold">{t("security.recoveryCodes")}</h2>
              <p>{t("security.recoveryWarning")}</p>
              <ul className="grid grid-cols-2 gap-x-4 gap-y-1">
                {setup.codes.map((code) => (
                  <li key={code}>
                    <bdi dir="ltr" className="font-mono">
                      {code}
                    </bdi>
                  </li>
                ))}
              </ul>
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() =>
                  void perform(async () => {
                    await navigator.clipboard.writeText(setup.codes.join("\n"));
                    setCopied(true);
                  })
                }
              >
                {t("security.copyCodes")}
              </Button>
              <p role="status">{copied && t("security.copied")}</p>
            </section>
          )}
          {(enabled || setup) && (
            <form
              className="grid gap-3 self-stretch"
              onSubmit={(event) => {
                event.preventDefault();
                const form = event.currentTarget;
                const fields = new FormData(form);
                const code = String(fields.get("code"));
                void perform(async () => {
                  if (enabled) {
                    await disableMfa({
                      code,
                      password: String(fields.get("password")),
                    });
                  } else {
                    await confirmMfaEnrollment({ code });
                  }
                  setSetup(null);
                  form.reset();
                  await client.invalidateQueries({ queryKey: meQueryKey });
                });
              }}
            >
              {enabled && (
                <h2 className="font-semibold">{t("security.disable")}</h2>
              )}
              {enabled && (
                <Input
                  label={t("auth.signIn.passwordLabel")}
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  maxLength={256}
                  required
                />
              )}
              <Input
                label={t("auth.mfa.codeLabel")}
                name="code"
                dir="ltr"
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]{6}"
                maxLength={6}
                required
              />
              <Button
                type="submit"
                variant={enabled ? "secondary" : "primary"}
                disabled={busy}
                className={
                  enabled
                    ? "justify-self-start border-missing text-missing"
                    : "justify-self-start"
                }
              >
                {t(enabled ? "security.disable" : "security.confirm")}
              </Button>
            </form>
          )}
        </>
      )}
    </div>
  );
}
