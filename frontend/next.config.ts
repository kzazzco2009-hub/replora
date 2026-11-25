import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

/**
 * Dev-only proxy so same-origin cookies/CSRF work without CORS.
 * The production rewrite is P19.1 (Vercel).
 */
export function apiRewrites(
  nodeEnv: string | undefined,
  backendOrigin: string | undefined,
) {
  if (nodeEnv !== "development") {
    return [];
  }
  const origin = backendOrigin ?? "http://localhost:8000";
  return [{ source: "/api/:path*", destination: `${origin}/api/:path*` }];
}

const nextConfig: NextConfig = {
  async rewrites() {
    return apiRewrites(process.env.NODE_ENV, process.env.BACKEND_ORIGIN);
  },
};

const withNextIntl = createNextIntlPlugin();

export default withNextIntl(nextConfig);
