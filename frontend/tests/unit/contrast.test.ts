import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

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

function hexOf(themeBlock: string, token: string): string {
  const match = themeBlock.match(
    new RegExp(`${token}:\\s*(#[0-9a-f]{6});`, "i"),
  );
  if (!match) {
    throw new Error(`${token} is not a literal hex value in this block`);
  }
  return match[1];
}

function srgbToLinear(channel: number): number {
  const c = channel / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function relativeLuminance(hex: string): number {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return (
    0.2126 * srgbToLinear(r) +
    0.7152 * srgbToLinear(g) +
    0.0722 * srgbToLinear(b)
  );
}

function contrastRatio(hexA: string, hexB: string): number {
  const a = relativeLuminance(hexA);
  const b = relativeLuminance(hexB);
  const lighter = Math.max(a, b);
  const darker = Math.min(a, b);
  return (lighter + 0.05) / (darker + 0.05);
}

const lightBlock = block(tokensCss, '[data-theme="light"]');
const darkBlock = block(tokensCss, '[data-theme="dark"]');

/**
 * WCAG 2.2 AA rule applied per pair (T11.3, design.md §3/§9):
 * - TEXT_MIN (4.5:1): ink and ink-muted read as body text on bg/surface/
 *   surface-raised; petrol-contrast and saffron-contrast are the text
 *   printed directly on a solid petrol/saffron button fill.
 * - UI_MIN (3:1): petrol, ok, diff, missing and review on bg/surface are
 *   never the sole carrier of meaning (design.md §3: "status is never
 *   shown by color alone" — an icon + text label in --ink always goes with
 *   them), so here they are treated as non-text UI indicators (icons,
 *   borders, chip fills), per WCAG 1.4.11.
 */
const TEXT_MIN = 4.5;
const UI_MIN = 3.0;

const textPairs: Array<[string, string]> = [
  ["--ink", "--bg"],
  ["--ink", "--surface"],
  ["--ink", "--surface-raised"],
  ["--ink-muted", "--bg"],
  ["--ink-muted", "--surface"],
  ["--ink-muted", "--surface-raised"],
  ["--petrol-contrast", "--petrol"],
  ["--saffron-contrast", "--saffron"],
];

const uiPairs: Array<[string, string]> = [
  ["--petrol", "--bg"],
  ["--petrol", "--surface"],
  ["--ok", "--bg"],
  ["--ok", "--surface"],
  ["--diff", "--bg"],
  ["--diff", "--surface"],
  ["--missing", "--bg"],
  ["--missing", "--surface"],
  ["--review", "--bg"],
  ["--review", "--surface"],
];

describe.each([
  ["light", lightBlock],
  ["dark", darkBlock],
])("token contrast in %s theme", (_themeName, themeBlock) => {
  it.each(textPairs)("%s on %s is >= 4.5:1 (text)", (fg, bg) => {
    const ratio = contrastRatio(hexOf(themeBlock, fg), hexOf(themeBlock, bg));
    expect(ratio).toBeGreaterThanOrEqual(TEXT_MIN);
  });

  it.each(uiPairs)("%s on %s is >= 3:1 (UI/status)", (fg, bg) => {
    const ratio = contrastRatio(hexOf(themeBlock, fg), hexOf(themeBlock, bg));
    expect(ratio).toBeGreaterThanOrEqual(UI_MIN);
  });
});
