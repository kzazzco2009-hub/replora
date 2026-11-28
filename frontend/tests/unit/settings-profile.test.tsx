import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import SettingsPage from "../../src/app/[locale]/(app)/settings/page";
import { meQueryKey, type Me } from "../../src/lib/api/use-me";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

const { replace, setTheme } = vi.hoisted(() => ({
  replace: vi.fn(),
  setTheme: vi.fn(),
}));
vi.mock("@/i18n/routing", () => ({
  usePathname: () => "/settings",
  useRouter: () => ({ replace }),
}));
vi.mock("next-themes", () => ({ useTheme: () => ({ setTheme }) }));

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
  document.cookie = "replora_csrf=test-token";
});

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("profile settings ($dir)", ({ dir, locale, messages }) => {
  const labels = messages.settings;

  async function showProfile() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <QueryClientProvider client={client}>
            <SettingsPage />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
    await screen.findByLabelText(labels.display_name);
    return {
      client,
      language: screen.getByLabelText<HTMLSelectElement>(labels.locale),
      save: screen.getByRole<HTMLButtonElement>("button", {
        name: labels.save,
      }),
    };
  }

  it("prefills the form and saves only edited preferences with CSRF", async () => {
    const patch = vi.fn();
    server.use(
      http.patch("/api/v1/auth/me", async ({ request }) => {
        patch(
          await request.clone().json(),
          request.headers.get("X-CSRF-Token"),
        );
      }),
    );
    const { client, language, save } = await showProfile();
    expect(
      screen.getByLabelText<HTMLInputElement>(labels.display_name).value,
    ).toBe("سلمى");
    expect(language.value).toBe("ar");
    expect(
      screen.getByLabelText<HTMLSelectElement>(labels.timezone).value,
    ).toBe("Africa/Cairo");
    expect(
      screen.getByText("Africa/Cairo", { selector: "bdi[dir=ltr]" }),
    ).toBeTruthy();
    expect(
      screen.getByRole<HTMLInputElement>("radio", {
        name: messages.theme.toggle.system,
      }).checked,
    ).toBe(true);
    expect(save.disabled).toBe(true);

    fireEvent.change(language, { target: { value: "en" } });
    fireEvent.click(
      screen.getByRole("radio", { name: messages.theme.toggle.dark }),
    );
    fireEvent.click(save);

    await waitFor(() =>
      expect(screen.getByRole("status").textContent).toBe(labels.saved),
    );
    expect(patch).toHaveBeenCalledExactlyOnceWith(
      { locale: "en", theme: "dark" },
      "test-token",
    );
    expect(replace).toHaveBeenCalledWith("/settings", { locale: "en" });
    expect(setTheme).toHaveBeenCalledWith("dark");
    expect(client.getQueryData<Me>(meQueryKey)?.memberships).toHaveLength(1);
    expect(save.disabled).toBe(true);
  });

  it("maps a 422 to the translated language field message", async () => {
    setScenario("auth_update_me", "invalid_locale");
    const { language, save } = await showProfile();
    fireEvent.change(language, { target: { value: "en" } });
    fireEvent.click(save);
    const error = await screen.findByText(
      messages.errors.validation.LITERAL_ERROR,
    );
    expect(language.getAttribute("aria-invalid")).toBe("true");
    expect(language.getAttribute("aria-describedby")).toBe(error.id);
    expect(replace).not.toHaveBeenCalled();
    expect(screen.getByRole("status").textContent).toBe("");
  });
});
