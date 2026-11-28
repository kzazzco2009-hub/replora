import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import enrollment from "../../../contracts/fixtures/auth/auth_enroll_mfa.json";
import me from "../../../contracts/fixtures/auth/auth_get_me.json";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import SecurityPage from "../../src/app/[locale]/(app)/settings/security/page";
import { getScenario, setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

vi.mock("@/i18n/routing", () => ({ useRouter: () => ({ replace: vi.fn() }) }));
afterEach(() => vi.restoreAllMocks());

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("security settings ($dir)", ({ dir, locale, messages }) => {
  it("enrolls, retries an invalid code, refreshes status, and disables MFA", async () => {
    const t = messages.security;
    const codeLabel = messages.auth.mfa.codeLabel;
    const confirm = vi.fn();
    const disable = vi.fn();
    const readMe = vi.fn();
    let enabled = false;
    server.use(
      http.get("/api/v1/auth/me", () => {
        readMe();
        return HttpResponse.json({ ...me.ok.body, mfa_enabled: enabled });
      }),
      http.post("/api/v1/auth/mfa/enroll/confirm", async ({ request }) => {
        confirm(await request.clone().json());
        if (getScenario("auth_confirm_mfa") === "ok") enabled = true;
      }),
      http.delete("/api/v1/auth/mfa", async ({ request }) => {
        disable(await request.clone().json());
        enabled = false;
      }),
    );

    document.cookie = "replora_csrf=test-token";
    const storage = vi.spyOn(Storage.prototype, "setItem");
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <SecurityPage />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );

    fireEvent.click(await screen.findByRole("button", { name: t.enable }));
    await screen.findByText(t.recoveryWarning);
    const { otpauth_uri, recovery_codes } = enrollment.ok.body;
    const secret = new URL(otpauth_uri).searchParams.get("secret")!;
    const options = { selector: 'bdi[dir="ltr"]' };
    expect(screen.getByText(secret, options)).toBeTruthy();
    for (const code of recovery_codes) {
      expect(screen.getAllByText(code, options)).toHaveLength(1);
    }
    expect(
      screen.getByRole("link", { name: t.openApp }).getAttribute("href"),
    ).toBe(otpauth_uri);

    function enterCode(code: string, button: string) {
      fireEvent.change(screen.getByLabelText(codeLabel), {
        target: { value: code },
      });
      fireEvent.click(screen.getByRole("button", { name: button }));
    }

    setScenario("auth_confirm_mfa", "mfa_code_invalid");
    enterCode("000000", t.confirm);
    expect(await screen.findByRole("alert")).toHaveProperty(
      "textContent",
      t.invalidCode,
    );
    expect(screen.getByText(t.recoveryWarning)).toBeTruthy();

    setScenario("auth_confirm_mfa", "ok");
    enterCode("123456", t.confirm);
    await screen.findByText(t.enabled);
    expect(confirm).toHaveBeenLastCalledWith({ code: "123456" });
    expect(readMe).toHaveBeenCalledTimes(2);
    expect(screen.queryByText(secret, options)).toBeNull();
    expect(screen.queryByText(t.recoveryWarning)).toBeNull();
    for (const code of recovery_codes)
      expect(screen.queryByText(code, options)).toBeNull();

    fireEvent.change(
      screen.getByLabelText(messages.auth.signIn.passwordLabel),
      {
        target: { value: "test-password" },
      },
    );
    enterCode("654321", t.disable);
    await screen.findByText(t.disabled);
    expect(disable).toHaveBeenCalledWith({
      password: "test-password",
      code: "654321",
    });
    expect(readMe).toHaveBeenCalledTimes(3);
    expect(storage).not.toHaveBeenCalled();
  });
});
