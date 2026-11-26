import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { useMe } from "../../src/lib/api/use-me";
import { setScenario } from "../msw/scenarios";

/** No retry here: the retry policy itself is covered by query-provider.test.tsx. */
function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
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

describe("useMe", () => {
  it("resolves the current user on the ok scenario", async () => {
    renderWithClient(<MeProbe />);

    await waitFor(() => {
      expect(screen.getByText("salma@example.com")).toBeTruthy();
    });
  });

  it("surfaces an ApiError the caller can read, on the unauthenticated scenario", async () => {
    setScenario("auth_get_me", "unauthenticated");
    renderWithClient(<MeProbe />);

    await waitFor(() => {
      expect(screen.getByText("Error: Unauthorized")).toBeTruthy();
    });
  });
});
