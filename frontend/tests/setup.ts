import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

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
