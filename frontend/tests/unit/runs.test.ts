import { http, HttpResponse } from "msw";
import { beforeEach, expect, it } from "vitest";
import {
  approveRun,
  createRun,
  runErrorMessages,
} from "../../src/lib/api/runs";
import { PLAN_HASH, RUN_ID, run } from "../msw/handlers/runs";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

const options = { wsId: "ws-1", idempotencyKey: "review-click" };
const path = "/api/v1/workspaces/ws-1/runs";

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
});

it("creates from the draft and approves the exact plan with separate idempotency keys", async () => {
  server.use(
    http.post(path, async ({ request }) => {
      expect(request.headers.get("Idempotency-Key")).toBe("review-click");
      expect(await request.json()).toEqual({ draft_id: "draft-1" });
      return HttpResponse.json(run, { status: 201 });
    }),
    http.post(`${path}/${RUN_ID}/approve`, async ({ request }) => {
      expect(request.headers.get("Idempotency-Key")).toBe("approve-click");
      expect(await request.json()).toEqual({ plan_hash: PLAN_HASH });
      return HttpResponse.json({ ...run, state: "QUEUED" }, { status: 202 });
    }),
  );
  const created = await createRun("draft-1", options);
  expect(created.state).toBe("AWAITING_APPROVAL");
  await expect(
    approveRun(created.id, created.plan_hash, {
      ...options,
      idempotencyKey: "approve-click",
    }),
  ).resolves.toMatchObject({ state: "QUEUED" });
});

it("maps draft issues and omits problem detail", async () => {
  setScenario("runs_create", "DRAFT_INVALID");
  const messages = await createRun("draft-1", options).catch(runErrorMessages);
  expect(messages).toMatchObject([
    { messageKey: "errors.problem.DRAFT_INVALID" },
    { messageKey: "errors.validation.MISSING" },
  ]);
  expect(JSON.stringify(messages)).not.toContain("internal detail");
});

it.each(["PLAN_HASH_MISMATCH", "INVALID_STATE_TRANSITION", "RATE_LIMITED"])(
  "maps approval failure %s",
  async (code) => {
    setScenario("runs_approve", code);
    const messages = await approveRun(RUN_ID, PLAN_HASH, options).catch(
      runErrorMessages,
    );
    expect(messages).toMatchObject([{ messageKey: `errors.problem.${code}` }]);
  },
);
