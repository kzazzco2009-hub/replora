import { useQueryClient, type QueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { useEffect } from "react";
import { describe, expect, it } from "vitest";
import { QueryProvider } from "../../src/components/providers/query-provider";
import { ApiError, type Problem } from "../../src/lib/api/problem";

function problem(status: number): Problem {
  return { type: "about:blank", title: "x", status, code: "INTERNAL_ERROR" };
}

function retryOf(client: QueryClient) {
  return client.getDefaultOptions().queries?.retry as (
    failureCount: number,
    error: unknown,
  ) => boolean;
}

function ClientProbe() {
  const client = useQueryClient();
  const options = client.getDefaultOptions().queries;
  const retry = retryOf(client);

  return (
    <div
      data-testid="probe"
      data-stale-time={options?.staleTime}
      data-refetch-on-focus={String(options?.refetchOnWindowFocus)}
      data-retry-4xx={String(retry(0, new ApiError(problem(400))))}
      data-retry-5xx-first={String(retry(0, new ApiError(problem(500))))}
      data-retry-5xx-capped={String(retry(2, new ApiError(problem(500))))}
      data-retry-network={String(retry(0, new Error("network down")))}
    />
  );
}

describe("QueryProvider", () => {
  it("renders its children", () => {
    render(
      <QueryProvider>
        <p>content</p>
      </QueryProvider>,
    );

    expect(screen.getByText("content")).toBeTruthy();
  });

  it("sets staleTime and disables refetchOnWindowFocus", () => {
    render(
      <QueryProvider>
        <ClientProbe />
      </QueryProvider>,
    );

    const probe = screen.getByTestId("probe");
    expect(probe.getAttribute("data-stale-time")).toBe("30000");
    expect(probe.getAttribute("data-refetch-on-focus")).toBe("false");
  });

  it("never retries a 4xx ApiError, retries a 5xx up to the cap, and retries other errors", () => {
    render(
      <QueryProvider>
        <ClientProbe />
      </QueryProvider>,
    );

    const probe = screen.getByTestId("probe");
    expect(probe.getAttribute("data-retry-4xx")).toBe("false");
    expect(probe.getAttribute("data-retry-5xx-first")).toBe("true");
    expect(probe.getAttribute("data-retry-5xx-capped")).toBe("false");
    expect(probe.getAttribute("data-retry-network")).toBe("true");
  });

  it("creates an independent QueryClient per provider instance", () => {
    const captured: Partial<Record<"a" | "b", QueryClient>> = {};

    function Capture({ into }: { into: "a" | "b" }) {
      const client = useQueryClient();
      useEffect(() => {
        captured[into] = client;
      }, [client, into]);
      return null;
    }

    render(
      <>
        <QueryProvider>
          <Capture into="a" />
        </QueryProvider>
        <QueryProvider>
          <Capture into="b" />
        </QueryProvider>
      </>,
    );

    expect(captured.a).not.toBe(captured.b);
  });
});
