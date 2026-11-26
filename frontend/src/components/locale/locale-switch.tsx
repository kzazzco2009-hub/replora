"use client";

import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/routing";

const LOCALES = ["ar", "en"] as const;

export function LocaleSwitch() {
  const t = useTranslations("localeSwitch");
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div role="group" aria-label={t("groupLabel")} className="flex gap-1">
      {LOCALES.map((target) => (
        <button
          key={target}
          type="button"
          lang={target}
          aria-pressed={locale === target}
          onClick={() => router.replace(pathname, { locale: target })}
          className="flex min-h-11 min-w-11 items-center justify-center rounded-control px-2 text-sm font-medium outline-offset-2 focus-visible:outline-2 focus-visible:outline-focus-ring"
        >
          {t(target)}
        </button>
      ))}
    </div>
  );
}
