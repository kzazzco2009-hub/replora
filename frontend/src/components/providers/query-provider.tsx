"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { isApiError } from "@/lib/api/problem";

/**
 * No retry for a 4xx ApiError (the request is wrong or unauthenticated, and
 * repeating it changes nothing); up to 2 retries otherwise (a 5xx or a
 * network failure, which may be transient).
 */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (isApiError(error) && error.problem.status < 500) return false;
  return failureCount < 2;
}

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: shouldRetry,
      },
    },
  });
}

/**
 * The QueryClient is created with useState, not at module scope: module
 * scope would share one cache (and its data) across every user and request
 * on the server, since Next.js can reuse the module between requests.
 */
export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(createQueryClient);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
