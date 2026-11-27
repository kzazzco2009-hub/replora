import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LocaleSwitch } from "../../src/components/locale/locale-switch";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";

const replace = vi.fn();
let pathname: string;

vi.mock("next/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("next/navigation")>()),
  usePathname: () => pathname,
  useRouter: () => ({ replace }),
}));

afterEach(() => {
  replace.mockClear();
  document.cookie = "NEXT_LOCALE=; path=/; max-age=0";
});

describe.each([
  { locale: "en", dir: "ltr", target: "ar", messages: en },
  { locale: "ar", dir: "rtl", target: "en", messages: ar },
] as const)("LocaleSwitch (dir=$dir)", ({ locale, dir, target, messages }) => {
  function renderSwitch(path: string) {
    pathname = `/${locale}${path}`;
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <LocaleSwitch />
        </NextIntlClientProvider>
      </div>,
    );
  }

  it.each(["", "/tokens-preview"])(
    "keeps the page at path %j when switching locale",
    (path) => {
      renderSwitch(path);
      fireEvent.click(
        screen.getByRole("button", { name: messages.localeSwitch[target] }),
      );
      expect(replace).toHaveBeenCalledExactlyOnceWith(`/${target}${path}`);
    },
  );
});
