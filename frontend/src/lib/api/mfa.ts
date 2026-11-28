import { getApiClient } from "./client";
import type { components } from "./schema";

export type MfaEnrollment = components["schemas"]["MfaEnrollment"];

export async function enrollMfa(): Promise<MfaEnrollment> {
  const { data } = await getApiClient().POST("/api/v1/auth/mfa/enroll");
  if (!data) throw new Error("Missing MFA enrollment response");
  return data;
}

export async function confirmMfaEnrollment(
  body: components["schemas"]["MfaCodeRequest"],
) {
  await getApiClient().POST("/api/v1/auth/mfa/enroll/confirm", { body });
}

export async function disableMfa(
  body: components["schemas"]["MfaDisableRequest"],
) {
  await getApiClient().DELETE("/api/v1/auth/mfa", { body });
}
