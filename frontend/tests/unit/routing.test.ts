import { describe, expect, it } from "vitest";
import { localeDirection, routing } from "../../src/i18n/routing";

describe("routing", () => {
  it("defaults to English (D10: cookie, then Accept-Language, then en)", () => {
    expect(routing.defaultLocale).toBe("en");
  });

  it("supports ar and en", () => {
    expect(routing.locales).toEqual(["ar", "en"]);
  });
});

describe("localeDirection", () => {
  it("is rtl for ar", () => {
    expect(localeDirection("ar")).toBe("rtl");
  });

  it("is ltr for en", () => {
    expect(localeDirection("en")).toBe("ltr");
  });
});
