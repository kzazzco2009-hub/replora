import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ComponentProps } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ForgotPasswordForm } from "../../src/components/features/auth/forgot-password-form";
import messages from "../../messages/en.json";
import { setScenario } from "../msw/scenarios";

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
          <ForgotPasswordForm />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
}

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "salma@example.com" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send reset link" }));
}

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
});

describe.each(["ltr", "rtl"] as const)("ForgotPasswordForm (dir=%s)", (dir) => {
  it("has an accessible name for email", () => {
    renderForm(dir);

    expect(screen.getByLabelText("Email")).toBeTruthy();
  });
});

describe("ForgotPasswordForm behavior", () => {
  it("shows the same neutral success state for an ok response", async () => {
    setScenario("auth_forgot_password", "ok");
    renderForm();
    fillAndSubmit();

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Check your email" }),
      ).toBeTruthy();
    });
  });

  it("puts a 422 error on the email field instead of the success state", async () => {
    setScenario("auth_forgot_password", "invalid_email");
    renderForm();
    fillAndSubmit();

    await waitFor(() => {
      expect(screen.getByLabelText("Email").getAttribute("aria-invalid")).toBe(
        "true",
      );
    });
    expect(
      screen.queryByRole("heading", { name: "Check your email" }),
    ).toBeNull();
  });

  it("shows a 429 as the generic rate-limit message, never the success state", async () => {
    setScenario("auth_forgot_password", "rate_limited");
    renderForm();
    fillAndSubmit();

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "Too many attempts",
      );
    });
    expect(
      screen.queryByRole("heading", { name: "Check your email" }),
    ).toBeNull();
  });
});
