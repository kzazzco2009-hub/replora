import { readFileSync } from "node:fs";
import { join } from "node:path";
import { http, HttpResponse } from "msw";
import { getScenario } from "../scenarios";

type Method = "get" | "post" | "patch" | "delete";
type FixtureCase = { status: number; body: unknown };
type Fixture = Record<string, FixtureCase>;

const FIXTURES_DIR = join(
  import.meta.dirname,
  "..",
  "..",
  "..",
  "..",
  "contracts",
  "fixtures",
  "auth",
);

// fixture key (contracts/fixtures/auth/<key>.json) -> method + path. Each
// key is the operationId openapi-typescript derives from the matching
// FastAPI route stub, so a new auth endpoint needs one line here plus its
// fixture file, never new handler logic. A new *scenario* on an existing
// endpoint needs neither: it's picked up straight from the fixture JSON.
const ENDPOINTS: Record<string, { method: Method; path: string }> = {
  auth_get_csrf: { method: "get", path: "/api/v1/auth/csrf" },
  auth_register: { method: "post", path: "/api/v1/auth/register" },
  auth_login: { method: "post", path: "/api/v1/auth/login" },
  auth_logout: { method: "post", path: "/api/v1/auth/logout" },
  auth_refresh: { method: "post", path: "/api/v1/auth/refresh" },
  auth_get_me: { method: "get", path: "/api/v1/auth/me" },
  auth_delete_me: { method: "delete", path: "/api/v1/auth/me" },
  auth_update_me: { method: "patch", path: "/api/v1/auth/me" },
  auth_verify_email: { method: "post", path: "/api/v1/auth/verify-email" },
  auth_forgot_password: {
    method: "post",
    path: "/api/v1/auth/password/forgot",
  },
  auth_reset_password: {
    method: "post",
    path: "/api/v1/auth/password/reset",
  },
  auth_enroll_mfa: { method: "post", path: "/api/v1/auth/mfa/enroll" },
  auth_confirm_mfa: {
    method: "post",
    path: "/api/v1/auth/mfa/enroll/confirm",
  },
  auth_mfa_challenge: { method: "post", path: "/api/v1/auth/mfa/challenge" },
  auth_disable_mfa: { method: "delete", path: "/api/v1/auth/mfa" },
  auth_start_export: { method: "post", path: "/api/v1/auth/me/export" },
  auth_get_export: {
    method: "get",
    path: "/api/v1/auth/me/export/:exportId",
  },
  auth_list_sessions: { method: "get", path: "/api/v1/auth/sessions" },
  auth_revoke_session: {
    method: "delete",
    path: "/api/v1/auth/sessions/:sessionId",
  },
};

function loadFixture(key: string): Fixture {
  return JSON.parse(
    readFileSync(join(FIXTURES_DIR, `${key}.json`), "utf8"),
  ) as Fixture;
}

export const authHandlers = Object.entries(ENDPOINTS).map(
  ([key, { method, path }]) => {
    const fixture = loadFixture(key);
    return http[method](path, () => {
      const { status, body } = fixture[getScenario(key)];
      return body === null
        ? new HttpResponse(null, { status })
        : HttpResponse.json(body, { status });
    });
  },
);
