import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import type { ComponentProps } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ResetPasswordForm } from "../../src/components/features/auth/reset-password-form";
import messages from "../../messages/en.json";
import { server } from "../msw/server";
import { setScenario } from "../msw/scenarios";

let searchParams = new URLSearchParams("token=a-reset-token");

vi.mock("next/navigation", () => ({
  useSearchParams: () => searchParams,
}));
vi.mock("@/i18n/routing", () => ({
  Link: ({ href, ...props }: ComponentProps<"a">) => (
    <a href={href} {...props} />
  ),
}));

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
});

function renderForm(dir: "ltr" | "rtl" = "ltr") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <div dir={dir}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <QueryClientProvider client={client}>
          <ResetPasswordForm />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
}

function fillAndSubmit(password = "a-strong-new-password") {
  fireEvent.change(screen.getByLabelText("New password"), {
    target: { value: password },
  });
  fireEvent.click(screen.getByRole("button", { name: "Reset password" }));
}

describe.each(["ltr", "rtl"] as const)("ResetPasswordForm (dir=%s)", (dir) => {
  it("has an accessible name for the new password field", () => {
    renderForm(dir);

    expect(screen.getByLabelText("New password")).toBeTruthy();
  });
});

describe("ResetPasswordForm behavior", () => {
  it("shows the missing-token state when there is no token, and never submits", () => {
    searchParams = new URLSearchParams();
    renderForm();

    expect(
      screen.getByRole("heading", { name: "Reset link incomplete" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("link", { name: "Request a new link" }),
    ).toBeTruthy();
    searchParams = new URLSearchParams("token=a-reset-token");
  });

  it("shows the success state with a link to sign in", async () => {
    setScenario("auth_reset_password", "ok");
    renderForm();
    fillAndSubmit();

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Password updated" }),
      ).toBeTruthy();
    });
    expect(screen.getByRole("link", { name: "Go to sign in" })).toBeTruthy();
  });

  it("shows a clear expired/used message and a link to request a new one for TOKEN_INVALID", async () => {
    setScenario("auth_reset_password", "token_invalid");
    renderForm();
    fillAndSubmit();

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "This link has expired or was already used",
      );
    });
    expect(
      screen.getByRole("link", { name: "Request a new link" }),
    ).toBeTruthy();
  });

  it("puts a STRING_TOO_SHORT 422 on the password field, keyed to the contract's `password` field", async () => {
    server.use(
      http.post("/api/v1/auth/password/reset", () =>
        HttpResponse.json(
          {
            type: "about:blank",
            title: "Validation failed",
            status: 422,
            code: "VALIDATION_FAILED",
            correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
            errors: [
              {
                path: "body.password",
                code: "STRING_TOO_SHORT",
                params: { min_length: 12 },
              },
            ],
          },
          { status: 422 },
        ),
      ),
    );
    renderForm();
    fillAndSubmit("short");

    await waitFor(() => {
      expect(
        screen.getByLabelText("New password").getAttribute("aria-invalid"),
      ).toBe("true");
    });
    expect(screen.getByText("Enter at least 12 characters.")).toBeTruthy();
  });
});
