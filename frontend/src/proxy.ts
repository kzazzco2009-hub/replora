import createMiddleware from "next-intl/middleware";
import { NextResponse, type NextRequest } from "next/server";
import { safeReturnTo } from "./lib/safe-return-to";
import { routing } from "./i18n/routing";

const intlMiddleware = createMiddleware(routing);

/** Pages reachable while signed out. */
const PUBLIC_SEGMENTS = new Set([
  "sign-in",
  "sign-up",
  "verify-email",
  "mfa",
  "forgot-password",
  "reset-password",
  "privacy",
  "terms",
]);

function firstSegment(pathname: string): string {
  const rest = pathname.startsWith("/") ? pathname.slice(1) : pathname;
  const slash = rest.indexOf("/");
  return slash === -1 ? rest : rest.slice(0, slash);
}

/**
 * S-64: UX only, never a security boundary — only presence is checked,
 * never the cookies' contents. Either cookie counts as "maybe signed in",
 * since the client's refresh flow (client.ts) handles an expired access
 * cookie; the server is the real gate on every API call.
 */
function hasSession(request: NextRequest): boolean {
  return (
    request.cookies.has("replora_access") ||
    request.cookies.has("replora_refresh")
  );
}

export default function proxy(request: NextRequest): NextResponse {
  const response = intlMiddleware(request);
  const isRedirect = response.status >= 300 && response.status < 400;
  if (isRedirect) return response;

  const { pathname, search } = request.nextUrl;
  const locale = firstSegment(pathname);
  const page = firstSegment(pathname.slice(1 + locale.length));

  if (PUBLIC_SEGMENTS.has(page) || hasSession(request)) return response;

  const signIn = request.nextUrl.clone();
  signIn.pathname = `/${locale}/sign-in`;
  signIn.search = "";
  const returnTo = safeReturnTo(pathname + search, locale);
  if (returnTo) signIn.searchParams.set("returnTo", returnTo);
  return NextResponse.redirect(signIn);
}

export const config = {
  matcher: "/((?!api|_next|_vercel|.*\\..*).*)",
};
