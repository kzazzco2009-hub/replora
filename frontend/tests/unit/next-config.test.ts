import { describe, expect, it } from "vitest";
import { apiRewrites } from "../../next.config";

describe("apiRewrites", () => {
  it("proxies /api/* to the default backend origin in development", () => {
    expect(apiRewrites("development", undefined)).toEqual([
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
    ]);
  });

  it("proxies to BACKEND_ORIGIN when set in development", () => {
    expect(apiRewrites("development", "http://backend:9000")).toEqual([
      { source: "/api/:path*", destination: "http://backend:9000/api/:path*" },
    ]);
  });

  it("has no rewrite in production", () => {
    expect(apiRewrites("production", undefined)).toEqual([]);
  });
});
