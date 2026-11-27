import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { MfaForm } from "../../src/components/features/auth/mfa-form";
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

function renderForm(dir: "ltr" | "rtl" = "ltr") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <div dir={dir}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <QueryClientProvider client={client}>
          <MfaForm />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
}

beforeEach(() => {
  replace.mockClear();
  searchParams = new URLSearchParams("returnTo=%2Fen%2Fdashboard");
  document.cookie = "replora_csrf=test-token";
});

describe.each(["ltr", "rtl"] as const)("MfaForm (dir=%s)", (dir) => {
  it("has an accessible name for the code field, and a recovery-code toggle", () => {
    renderForm(dir);

    expect(screen.getByLabelText("Verification code")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Use a recovery code instead" }),
    ).toBeTruthy();
  });
});

describe("MfaForm behavior", () => {
  it("verifies a code and redirects to the returnTo path", async () => {
    setScenario("auth_mfa_challenge", "ok");
    renderForm();
    fireEvent.change(screen.getByLabelText("Verification code"), {
      target: { value: "123456" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Verify" }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/en/dashboard"));
  });

  it("sends exactly recovery_code when the recovery toggle is on", async () => {
    let body: unknown;
    server.use(
      http.post("/api/v1/auth/mfa/challenge", async ({ request }) => {
        body = await request.json();
        return HttpResponse.json(
          { email: "salma@example.com" },
          { status: 200 },
        );
      }),
    );
    renderForm();
    fireEvent.click(
      screen.getByRole("button", { name: "Use a recovery code instead" }),
    );
    fireEvent.change(screen.getByLabelText("Recovery code"), {
      target: { value: "r3c0v3ry" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Verify" }));

    await waitFor(() => expect(body).toEqual({ recovery_code: "r3c0v3ry" }));
  });

  it("stays on the form with a message for MFA_CODE_INVALID", async () => {
    setScenario("auth_mfa_challenge", "mfa_code_invalid");
    renderForm();
    fireEvent.change(screen.getByLabelText("Verification code"), {
      target: { value: "000000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Verify" }));

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain("didn't match");
    });
    expect(replace).not.toHaveBeenCalled();
  });

  it("redirects to sign-in with a visible message for MFA_CHALLENGE_INVALID", async () => {
    setScenario("auth_mfa_challenge", "challenge_invalid");
    renderForm();
    fireEvent.change(screen.getByLabelText("Verification code"), {
      target: { value: "123456" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Verify" }));

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith(
        "/en/sign-in?returnTo=%2Fen%2Fdashboard&challengeExpired=1",
      ),
    );
  });

  it("leaves the step with the back link, keeping returnTo", () => {
    renderForm();
    fireEvent.click(screen.getByRole("button", { name: "Back to sign in" }));

    expect(replace).toHaveBeenCalledWith(
      "/en/sign-in?returnTo=%2Fen%2Fdashboard",
    );
  });
});
