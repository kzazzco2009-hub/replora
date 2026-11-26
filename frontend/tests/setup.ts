import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, vi } from "vitest";
import { resetScenarios } from "./msw/scenarios";
import { server } from "./msw/server";

afterEach(cleanup);

// next/font/google's real module is empty outside Next's own compiler
// plugin, which rewrites the call at build time; Vitest never runs that
// plugin, so it's mocked the way Next.js's own testing docs recommend.
vi.mock("next/font/google", () => ({
  Readex_Pro: () => ({
    variable: "--font-readex-pro",
    className: "mock-readex-pro",
  }),
}));

// msw/node only: no public/mockServiceWorker.js and no browser worker
// registration (security decision — anything in public/ ships to prod).
// msw 3.x renamed `onUnhandledRequest` to `onUnhandledFrame`.
beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
afterEach(() => {
  server.resetHandlers();
  resetScenarios();
});
afterAll(() => server.close());
