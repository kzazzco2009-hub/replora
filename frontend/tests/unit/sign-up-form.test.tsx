import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ComponentProps } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SignUpForm } from "../../src/components/features/auth/sign-up-form";
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
          <SignUpForm />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
}

function fillAndSubmit() {
  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "salma@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Display name"), {
    target: { value: "Salma" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "a-strong-password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
}

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
});

describe.each(["ltr", "rtl"] as const)("SignUpForm (dir=%s)", (dir) => {
  it("has accessible names for email, display name and password", () => {
    renderForm(dir);

    expect(screen.getByLabelText("Email")).toBeTruthy();
    expect(screen.getByLabelText("Display name")).toBeTruthy();
    expect(screen.getByLabelText("Password")).toBeTruthy();
  });
});

describe("SignUpForm behavior", () => {
  it("shows the same neutral success state for an ok response", async () => {
    setScenario("auth_register", "ok");
    renderForm();
    fillAndSubmit();

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Check your email" }),
      ).toBeTruthy();
    });
  });

  it("puts 422 errors on the right fields instead of the success state", async () => {
    setScenario("auth_register", "invalid_email");
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

  it("shows a 429 as a form alert instead of the success state", async () => {
    setScenario("auth_register", "rate_limited");
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
