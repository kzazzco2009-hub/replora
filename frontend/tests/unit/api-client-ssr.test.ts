// @vitest-environment node
import { describe, expect, it } from "vitest";

describe("api client module (node environment, no `location`)", () => {
  it("importing it does not throw, since the client is built lazily", async () => {
    expect(typeof location).toBe("undefined");

    const mod = await import("../../src/lib/api/client");

    expect(mod.getApiClient).toBeTypeOf("function");
  });
});
