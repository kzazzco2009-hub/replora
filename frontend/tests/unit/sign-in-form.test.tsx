import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import type { ComponentProps } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SignInForm } from "../../src/components/features/auth/sign-in-form";
import messages from "../../messages/en.json";
import { server } from "../msw/server";
import { setScenario } from "../msw/scenarios";

const replace = vi.fn();
let searchParams = new URLSearchParams();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  useSearchParams: () => searchParams,
  useParams: () => ({ locale: "en" }),
}));
vi.mock("@/i18n/routing", () => ({
  Link: ({ href, ...props }: ComponentProps<"a">) => (
    <a href={href} {...props} />
  ),
}));

function renderForm(dir: "ltr" | "rtl" = "ltr") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <div dir={dir}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <QueryClientProvider client={client}>
          <SignInForm />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
}

function fillCredentials() {
  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "salma@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "correct-password" },
  });
}
function submit() {
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
}
beforeEach(() => {
  replace.mockClear();
  searchParams = new URLSearchParams();
  document.cookie = "replora_csrf=test-token";
});

describe.each(["ltr", "rtl"] as const)("SignInForm (dir=%s)", (dir) => {
  it("has accessible names for the email and password fields", () => {
    renderForm(dir);

    expect(screen.getByLabelText("Email")).toBeTruthy();
    expect(screen.getByLabelText("Password")).toBeTruthy();
  });

  it("shows a form alert as an icon plus text, with role=alert", async () => {
    setScenario("auth_login", "invalid_credentials");
    renderForm(dir);
    fillCredentials();
    submit();

    await waitFor(() => {
      const alert = screen.getByRole("alert");
      expect(alert.textContent).toContain("doesn't match our records");
      expect(alert.querySelector("svg")).not.toBeNull();
    });
  });
});

describe("SignInForm behavior", () => {
  it.each([
    ["returnTo=%2Fen%2Fdashboard", "/en/dashboard"],
    ["returnTo=https://evil.com", "/en"],
    ["", "/en"],
  ])(
    "redirects to %s -> %s after a successful sign-in",
    async (qs, expected) => {
      searchParams = new URLSearchParams(qs);
      renderForm();
      fillCredentials();
      submit();

      await waitFor(() => expect(replace).toHaveBeenCalledWith(expected));
    },
  );

  it("navigates to the MFA step on mfa_required, keeping returnTo", async () => {
    searchParams = new URLSearchParams("returnTo=%2Fen%2Fdashboard");
    setScenario("auth_login", "mfa_required");
    renderForm();
    fillCredentials();
    submit();

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith(
        "/en/mfa?returnTo=%2Fen%2Fdashboard",
      ),
    );
  });

  it.each([
    ["invalid_credentials", "doesn't match our records"],
    ["rate_limited", "Too many attempts"],
  ])("shows %s as a form alert", async (scenario, text) => {
    setScenario("auth_login", scenario);
    renderForm();
    fillCredentials();
    submit();

    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toContain(text),
    );
  });

  it("puts a 422 field error on the invalid input, linked by aria-describedby", async () => {
    server.use(
      http.post("/api/v1/auth/login", () =>
        HttpResponse.json(
          {
            type: "about:blank",
            title: "Validation failed",
            status: 422,
            code: "VALIDATION_FAILED",
            errors: [{ path: "body.email", code: "INVALID_EMAIL", params: {} }],
          },
          { status: 422 },
        ),
      ),
    );
    renderForm();
    fillCredentials();
    submit();

    await waitFor(() => {
      expect(screen.getByLabelText("Email").getAttribute("aria-invalid")).toBe(
        "true",
      );
    });
  });

  it("disables the submit button while pending, so a second click does nothing", async () => {
    let calls = 0;
    server.use(
      http.post("/api/v1/auth/login", async () => {
        calls += 1;
        await new Promise((resolve) => setTimeout(resolve, 20));
        return HttpResponse.json({ mfa_required: true }, { status: 200 });
      }),
    );
    renderForm();
    fillCredentials();
    const button = screen.getByRole<HTMLButtonElement>("button", {
      name: "Sign in",
    });
    fireEvent.click(button);
    await waitFor(() => expect(button.disabled).toBe(true));
    fireEvent.click(button);

    await waitFor(() => expect(calls).toBe(1));
  });
});
