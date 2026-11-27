import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { UserMenu } from "../../src/components/shell/user-menu";
import messages from "../../messages/en.json";
import { server } from "../msw/server";
import { setScenario } from "../msw/scenarios";

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  useParams: () => ({ locale: "en" }),
}));

function renderMenu(dir: "ltr" | "rtl" = "ltr") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const clear = vi.spyOn(client, "clear");
  const view = render(
    <div dir={dir}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <QueryClientProvider client={client}>
          <UserMenu />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
  return { ...view, clear };
}

function openMenu(container: HTMLElement) {
  const details = container.querySelector("details")!;
  fireEvent.click(details.querySelector("summary")!);
  return details;
}

beforeEach(() => {
  replace.mockClear();
  document.cookie = "replora_csrf=test-token";
});

describe.each(["ltr", "rtl"] as const)("UserMenu (dir=%s)", (dir) => {
  it("shows the signed-in user's display name and email once loaded, behind a disclosure", async () => {
    const { container } = renderMenu(dir);
    await screen.findByText("سلمى");

    const details = openMenu(container);
    expect(details.open).toBe(true);
    expect(screen.getByText("salma@example.com")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeTruthy();
  });
});

describe("UserMenu behavior", () => {
  it("clears the query cache and goes to sign-in on a successful sign-out", async () => {
    const { container, clear } = renderMenu();
    await screen.findByText("سلمى");
    openMenu(container);

    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/en/sign-in"));
    expect(clear).toHaveBeenCalled();
  });

  it("also goes to sign-in on a 401 (the session had already ended)", async () => {
    setScenario("auth_logout", "unauthenticated");
    const { container, clear } = renderMenu();
    await screen.findByText("سلمى");
    openMenu(container);

    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));

    await waitFor(() => expect(replace).toHaveBeenCalledWith("/en/sign-in"));
    expect(clear).toHaveBeenCalled();
  });

  it("shows other errors via mapProblem, never raw `detail`, and stays signed in", async () => {
    server.use(
      http.post("/api/v1/auth/logout", () =>
        HttpResponse.json(
          {
            type: "about:blank",
            title: "Forbidden",
            status: 403,
            code: "CSRF_FAILED",
            detail: "internal: token mismatch for session 01937a5e",
            correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
          },
          { status: 403 },
        ),
      ),
    );
    const { container } = renderMenu();
    await screen.findByText("سلمى");
    openMenu(container);

    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));

    await waitFor(() => {
      const alert = screen.getByRole("alert");
      expect(alert.textContent).toContain("This session needs to refresh");
      expect(alert.textContent).not.toContain("token mismatch");
    });
    expect(replace).not.toHaveBeenCalled();
  });
});
