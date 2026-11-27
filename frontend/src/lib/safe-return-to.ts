const MAX_LENGTH = 2048;

/** Pages a post-login returnTo must never point back into (redirect loops). */
const AUTH_SEGMENTS = new Set([
  "sign-in",
  "sign-up",
  "verify-email",
  "forgot-password",
  "reset-password",
  "mfa",
]);

function hasControlOrWhitespace(value: string): boolean {
  return /[\u0000-\u001f\u007f\s]/.test(value);
}

function looksLikeScheme(value: string): boolean {
  return /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(value);
}

/** Rejects anything that isn't an unambiguous same-origin, single-leading-slash path. */
function isSafeShape(value: string): boolean {
  return (
    !hasControlOrWhitespace(value) &&
    !value.includes("\\") &&
    !value.includes("@") &&
    value.startsWith("/") &&
    !value.startsWith("//") &&
    !looksLikeScheme(value)
  );
}

function firstSegment(pathname: string): string {
  const rest = pathname.slice(1);
  const slash = rest.indexOf("/");
  return slash === -1 ? rest : rest.slice(0, slash);
}

/**
 * Returns `value` unchanged if it is a safe same-origin relative path to
 * redirect back to after sign-in, or `null` otherwise. Checked on both the
 * raw string and its percent-decoded form, since an encoded "//" or "\n"
 * only becomes dangerous once a browser or router decodes it.
 */
export function safeReturnTo(value: unknown, locale: string): string | null {
  if (typeof value !== "string") return null;
  if (value.length === 0 || value.length > MAX_LENGTH) return null;
  if (!isSafeShape(value)) return null;

  let decoded: string;
  try {
    decoded = decodeURIComponent(value);
  } catch {
    return null;
  }
  if (!isSafeShape(decoded)) return null;

  const pathname = decoded.split(/[?#]/, 1)[0];
  if (firstSegment(pathname) !== locale) return null;

  const afterLocale = pathname.slice(1 + locale.length);
  if (AUTH_SEGMENTS.has(firstSegment(afterLocale))) return null;

  return value;
}
