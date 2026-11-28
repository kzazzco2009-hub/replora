"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { FormAlert } from "@/components/features/auth/form-alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { usePathname, useRouter } from "@/i18n/routing";
import { mapFieldErrors, type FieldError } from "@/lib/api/field-errors";
import { isApiError } from "@/lib/api/problem";
import { useMe, useUpdateMe, type Me } from "@/lib/api/use-me";
import SettingsLoading from "./loading";

const fields = ["display_name", "locale", "theme", "timezone"] as const;
type Profile = Pick<Me, (typeof fields)[number]>;
const themes = ["light", "dark", "system"] as const;
const timezones = Intl.supportedValuesOf("timeZone");
const languages = { ar: "العربية", en: "English" };
const noticeKey = "replora.profileSavedLocale";

// A locale change can remount the page and its query provider.
function localeNotice(locale: string, action: "read" | "write" | "clear") {
  try {
    if (action === "write") sessionStorage.setItem(noticeKey, locale);
    if (sessionStorage.getItem(noticeKey) !== locale) return false;
    if (action === "clear") sessionStorage.removeItem(noticeKey);
    return true;
  } catch {
    return false;
  }
}

export default function SettingsPage() {
  const t = useTranslations();
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const { setTheme } = useTheme();
  const client = useQueryClient();
  const me = useMe();
  const mutation = useUpdateMe();
  const [edits, setEdits] = useState<Partial<Profile>>({});
  const [saved, setSaved] = useState(() => localeNotice(locale, "read"));
  const problem = [me.error, mutation.error].find(
    (error) => isApiError(error) && error.problem.status === 401,
  );

  useEffect(() => {
    localeNotice(locale, "clear");
  }, [locale]);

  useEffect(() => {
    if (!problem) return;
    client.clear();
    router.replace("/sign-in");
  }, [client, problem, router]);

  if (me.isPending || problem) return <SettingsLoading />;

  const profile = me.data;
  if (!profile) {
    return (
      <div className="grid justify-items-start gap-4">
        <h1 className="text-xl font-semibold">{t("settings.profile")}</h1>
        <FormAlert title={t("settings.loadError")} />
        <Button
          variant="secondary"
          onClick={() => void me.refetch()}
          disabled={me.isFetching}
        >
          {t("runReview.retry")}
        </Button>
      </div>
    );
  }

  const values = { ...profile, ...edits };
  const changes = Object.fromEntries(
    fields
      .filter((name) => values[name] !== profile[name])
      .map((name) => [name, values[name]]),
  );
  const dirty = Object.keys(changes).length > 0;
  const validation =
    isApiError(mutation.error) && mutation.error.problem.status === 422
      ? mapFieldErrors(mutation.error.problem)
      : undefined;
  const message = (field?: FieldError) =>
    field &&
    t(field.messageKey, field.params as Record<string, string | number>);
  const hasFieldError = fields.some((name) => validation?.fields[name]);
  const alert =
    message(validation?.form[0]) ??
    (mutation.isError && !hasFieldError ? t("settings.saveError") : undefined);
  const themeError = message(validation?.fields.theme);

  function fieldMessage(name: keyof Profile, error?: string) {
    return error ? (
      <p id={`${name}-error`} role="alert" className="text-sm text-missing">
        {error}
      </p>
    ) : null;
  }

  function change<K extends keyof Profile>(name: K, value: Profile[K]) {
    setEdits((previous) => ({ ...previous, [name]: value }));
    setSaved(false);
    mutation.reset();
  }

  const zones = timezones.includes(values.timezone)
    ? timezones
    : [values.timezone, ...timezones];
  const options = {
    locale: Object.entries(languages),
    timezone: zones.map((zone) => [zone, zone]),
  };

  return (
    <div className="grid gap-4 [max-inline-size:36rem]">
      <h1 className="text-xl font-semibold">{t("settings.profile")}</h1>
      <Link
        href={`/${locale}/settings/security`}
        className="inline-flex items-center justify-self-start rounded-control text-petrol underline [min-block-size:44px] [min-inline-size:44px] focus-visible:outline-2 focus-visible:outline-focus-ring"
      >
        {t("security.heading")}
      </Link>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!dirty || mutation.isPending) return;
          mutation.mutate(changes, {
            onSuccess: (user) => {
              setEdits({});
              setSaved(true);
              if (user.theme !== profile.theme) setTheme(user.theme);
              if (user.locale !== profile.locale) {
                if (user.locale !== locale) localeNotice(user.locale, "write");
                router.replace(pathname, { locale: user.locale });
              }
            },
          });
        }}
      >
        <fieldset
          disabled={mutation.isPending}
          className="grid justify-items-stretch gap-4 rounded-panel border border-line p-4"
        >
          <Input
            label={t("settings.display_name")}
            autoComplete="name"
            required
            maxLength={100}
            value={values.display_name}
            error={message(validation?.fields.display_name)}
            onChange={(event) => change("display_name", event.target.value)}
          />
          {(["locale", "timezone"] as const).map((name) => {
            const error = message(validation?.fields[name]);
            return (
              <div key={name} className="grid gap-1.5">
                <label htmlFor={name} className="text-sm font-medium">
                  {t(`settings.${name}`)}
                </label>
                <select
                  id={name}
                  value={values[name]}
                  aria-invalid={error ? true : undefined}
                  aria-describedby={error ? `${name}-error` : undefined}
                  dir={name === "timezone" ? "ltr" : undefined}
                  className="rounded-control border border-line bg-surface px-3 [min-block-size:44px] focus-visible:outline-2 focus-visible:outline-focus-ring"
                  onChange={(event) => change(name, event.target.value)}
                >
                  {options[name].map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
                {name === "timezone" && (
                  <bdi dir="ltr" className="text-sm">
                    {values.timezone}
                  </bdi>
                )}
                {fieldMessage(name, error)}
              </div>
            );
          })}
          <fieldset>
            <legend className="text-sm font-medium">
              {t("theme.toggle.groupLabel")}
            </legend>
            <div className="flex flex-wrap gap-x-4">
              {themes.map((theme) => (
                <label
                  key={theme}
                  className="inline-flex items-center gap-2 [min-block-size:44px] [min-inline-size:44px]"
                >
                  <input
                    type="radio"
                    name="theme"
                    checked={values.theme === theme}
                    aria-describedby={themeError ? "theme-error" : undefined}
                    onChange={() => change("theme", theme)}
                  />
                  {t(`theme.toggle.${theme}`)}
                </label>
              ))}
            </div>
            {fieldMessage("theme", themeError)}
          </fieldset>
          {alert && <FormAlert title={alert} />}
          <Button
            type="submit"
            disabled={!dirty || mutation.isPending}
            aria-busy={mutation.isPending}
            className="justify-self-start motion-reduce:transition-none"
          >
            {t("settings.save")}
          </Button>
          <p role="status" className="text-sm text-ink">
            {saved ? t("settings.saved") : null}
          </p>
        </fieldset>
      </form>
    </div>
  );
}
