import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const designMd = readFileSync(
  path.resolve(import.meta.dirname, "../../../docs/design.md"),
  "utf-8",
);
const tokensCss = readFileSync(
  path.resolve(import.meta.dirname, "../../src/app/tokens.css"),
  "utf-8",
);

function block(css: string, selector: string): string {
  const start = css.indexOf(selector);
  if (start === -1) {
    throw new Error(`selector not found: ${selector}`);
  }
  const open = css.indexOf("{", start);
  const close = css.indexOf("}", open);
  return css.slice(open + 1, close);
}

const lightBlock = block(tokensCss, '[data-theme="light"]');
const darkBlock = block(tokensCss, '[data-theme="dark"]');

function valueOf(themeBlock: string, token: string): string | undefined {
  const match = themeBlock.match(new RegExp(`${token}:\\s*([^;]+);`, "i"));
  return match?.[1].trim().toLowerCase();
}

const hexPattern = /^#[0-9a-f]{6}$/i;

describe("color token parity with docs/design.md §3", () => {
  const rowPattern =
    /^\|\s*`(--[\w-]+)`\s*\|[^|]*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|$/gm;
  const rows = [...designMd.matchAll(rowPattern)];

  it("found the color table in docs/design.md", () => {
    expect(rows.length).toBeGreaterThan(5);
  });

  const hexRows = rows.filter(
    ([, , light, dark]) => hexPattern.test(light) && hexPattern.test(dark),
  );

  it.each(hexRows.map(([, token, light, dark]) => [token, light, dark]))(
    "%s matches design.md (light %s, dark %s)",
    (token, light, dark) => {
      expect(valueOf(lightBlock, token)).toBe(light.toLowerCase());
      expect(valueOf(darkBlock, token)).toBe(dark.toLowerCase());
    },
  );

  it("--focus-ring references --petrol in both themes, as design.md says", () => {
    expect(valueOf(lightBlock, "--focus-ring")).toBe("var(--petrol)");
    expect(valueOf(darkBlock, "--focus-ring")).toBe("var(--petrol)");
  });
});

describe('prefers-color-scheme fallback matches [data-theme="dark"]', () => {
  const fallbackBlock = block(tokensCss, ":root:not([data-theme])");
  const darkTokens = [...darkBlock.matchAll(/(--[\w-]+):/g)].map(
    ([, token]) => token,
  );

  it("has tokens to compare", () => {
    expect(darkTokens.length).toBeGreaterThan(5);
  });

  it.each(darkTokens)('%s matches [data-theme="dark"]', (token) => {
    expect(valueOf(fallbackBlock, token)).toBe(valueOf(darkBlock, token));
  });

  it("only applies without an explicit data-theme attribute", () => {
    expect(tokensCss).toContain("@media (prefers-color-scheme: dark)");
    expect(tokensCss).toContain(":root:not([data-theme])");
  });
});

describe("artifact-type color parity with docs/design.md §3", () => {
  const artifactLine = designMd.match(/\*\*Artifact type colors\*\*.*/)?.[0];
  if (!artifactLine) {
    throw new Error("artifact type colors line not found in docs/design.md");
  }

  const pairPattern = /(\w+)\s+`(#[0-9A-Fa-f]{6})`\/`(#[0-9A-Fa-f]{6})`/g;
  const pairs = [...artifactLine.matchAll(pairPattern)].map(
    ([, name, light, dark]) =>
      [`--artifact-${name.toLowerCase()}`, light, dark] as const,
  );

  it("found all 6 artifact-type colors in docs/design.md", () => {
    expect(pairs).toHaveLength(6);
  });

  it.each(pairs)(
    "%s matches design.md (light %s, dark %s)",
    (token, light, dark) => {
      expect(valueOf(lightBlock, token)).toBe(light.toLowerCase());
      expect(valueOf(darkBlock, token)).toBe(dark.toLowerCase());
    },
  );
});
