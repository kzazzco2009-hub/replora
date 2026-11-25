import { expectTypeOf, it } from "vitest";
import type { paths } from "../../src/lib/api/schema";

it("has /api/v1/auth/login (post) and /api/v1/health (get)", () => {
  expectTypeOf<paths["/api/v1/auth/login"]["post"]>().not.toBeNever();
  expectTypeOf<paths["/api/v1/health"]["get"]>().not.toBeNever();
});

it("types a 501 problem+json error response", () => {
  type LoginResponses = paths["/api/v1/auth/login"]["post"]["responses"];
  expectTypeOf<
    LoginResponses[501]["content"]["application/problem+json"]
  >().not.toBeNever();
});
