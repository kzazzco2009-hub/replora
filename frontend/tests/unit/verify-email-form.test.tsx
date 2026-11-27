import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import type { ComponentProps } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { VerifyEmailForm } from "../../src/components/features/auth/verify-email-form";
import messages from "../../messages/en.json";
import { server } from "../msw/server";
import { setScenario } from "../msw/scenarios";

let searchParams = new URLSearchParams("token=a-verify-token");

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
          <VerifyEmailForm />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
}

describe.each(["ltr", "rtl"] as const)("VerifyEmailForm (dir=%s)", (dir) => {
  it("shows the verified success state with a link to sign in", async () => {
    setScenario("auth_verify_email", "ok");
    renderForm(dir);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Email verified" }),
      ).toBeTruthy();
    });
    expect(screen.getByRole("link", { name: "Go to sign in" })).toBeTruthy();
  });
});

describe("VerifyEmailForm behavior", () => {
  it("shows a failure message for TOKEN_INVALID, with links out", async () => {
    setScenario("auth_verify_email", "token_invalid");
    renderForm();

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "We couldn't verify that link" }),
      ).toBeTruthy();
    });
    expect(screen.getByRole("alert").textContent).toContain(
      "This link has expired or was already used",
    );
    expect(
      screen.getByRole("link", { name: "Create a new account" }),
    ).toBeTruthy();
  });

  it("shows the missing-token state when there is no token, and never renders one", () => {
    searchParams = new URLSearchParams();
    renderForm();

    expect(
      screen.getByRole("heading", { name: "Verification link missing" }),
    ).toBeTruthy();
    searchParams = new URLSearchParams("token=a-verify-token");
  });

  it("posts the verify-email request exactly once", async () => {
    let calls = 0;
    server.use(
      http.post("/api/v1/auth/verify-email", () => {
        calls += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    renderForm();

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Email verified" }),
      ).toBeTruthy();
    });
    expect(calls).toBe(1);
  });
});
