import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { createQueryClient } from "../../src/components/providers/query-provider";
import { isApiError } from "../../src/lib/api/problem";
import { useMe } from "../../src/lib/api/use-me";
import { server } from "../msw/server";

/** No retry here: the retry policy itself is covered by query-provider.test.tsx. */
function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

/** The real provider defaults, but with retryDelay zeroed so a retrying test stays fast. */
function renderWithRealClient(ui: ReactElement) {
  const client = createQueryClient();
  client.setDefaultOptions({
    queries: { ...client.getDefaultOptions().queries, retryDelay: 0 },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
  );
}

function MeProbe() {
  const { data, error, isLoading } = useMe();
  if (isLoading) return <p>Loading…</p>;
  if (error) return <p>Error: {error.message}</p>;
  return <p>{data?.email}</p>;
}

function MeErrorCodeProbe() {
  const { error, isError } = useMe();
  if (!isError) return <p>pending</p>;
  return <p>{isApiError(error) ? error.problem.code : "not-an-api-error"}</p>;
}

describe("useMe", () => {
  it("resolves the current user on the ok scenario", async () => {
    renderWithClient(<MeProbe />);

    await waitFor(() => {
      expect(screen.getByText("salma@example.com")).toBeTruthy();
    });
  });

  it("does not retry a 401, and surfaces its UNAUTHENTICATED code", async () => {
    let calls = 0;
    server.use(
      http.get("/api/v1/auth/me", () => {
        calls += 1;
        return HttpResponse.json(
          {
            type: "about:blank",
            title: "Unauthorized",
            status: 401,
            code: "UNAUTHENTICATED",
          },
          { status: 401 },
        );
      }),
    );

    renderWithRealClient(<MeErrorCodeProbe />);

    await waitFor(() => {
      expect(screen.getByText("UNAUTHENTICATED")).toBeTruthy();
    });
    expect(calls).toBe(1);
  });

  it("retries a 500 before the error shows", async () => {
    let calls = 0;
    server.use(
      http.get("/api/v1/auth/me", () => {
        calls += 1;
        return HttpResponse.json(
          {
            type: "about:blank",
            title: "Internal Server Error",
            status: 500,
            code: "INTERNAL_ERROR",
          },
          { status: 500 },
        );
      }),
    );

    renderWithRealClient(<MeErrorCodeProbe />);

    await waitFor(() => {
      expect(screen.getByText("INTERNAL_ERROR")).toBeTruthy();
    });
    expect(calls).toBeGreaterThan(1);
  });
});
