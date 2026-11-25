import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const SRC_DIR = join(import.meta.dirname, "..", "..", "src");

const BANNED_PATTERNS: { re: RegExp; label: string }[] = [
  { re: /\bmargin-left\s*:/i, label: "margin-left" },
  { re: /\bmargin-right\s*:/i, label: "margin-right" },
  { re: /\bpadding-left\s*:/i, label: "padding-left" },
  { re: /\bpadding-right\s*:/i, label: "padding-right" },
  { re: /\bborder-left\s*:/i, label: "border-left" },
  { re: /\bborder-right\s*:/i, label: "border-right" },
  { re: /^\s*left\s*:/i, label: "left" },
  { re: /^\s*right\s*:/i, label: "right" },
  { re: /\btext-align\s*:\s*(left|right)\b/i, label: "text-align: left/right" },
  { re: /\bfloat\s*:\s*(left|right)\b/i, label: "float: left/right" },
];

const ALLOW_RE = /\/\*\s*logical-css-allow\s*:\s*\S.*?\*\//;

function findCssFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...findCssFiles(full));
    else if (entry.endsWith(".css")) out.push(full);
  }
  return out;
}

describe("logical CSS properties in src/**/*.css", () => {
  const cssFiles = findCssFiles(SRC_DIR);
  if (cssFiles.length === 0) throw new Error("no CSS files found under src/");

  for (const file of cssFiles) {
    it(`${file} has no physical-direction declarations`, () => {
      const lines = readFileSync(file, "utf8").split("\n");
      const violations: string[] = [];
      lines.forEach((line, index) => {
        if (ALLOW_RE.test(line)) return;
        for (const { re, label } of BANNED_PATTERNS) {
          if (re.test(line)) violations.push(`${file}:${index + 1} — ${label}`);
        }
      });
      expect(violations).toEqual([]);
    });
  }
});
