"use client";

import { type RefObject, useEffect, useRef, useState } from "react";

const baseTokens = [
  { token: "--bg", role: "app background" },
  { token: "--surface", role: "panels, tables" },
  { token: "--surface-raised", role: "dialogs, menus" },
  { token: "--ink", role: "primary text" },
  { token: "--ink-muted", role: "secondary text" },
  { token: "--line", role: "borders and dividers" },
] as const;

const accentTokens = [
  {
    bg: "--petrol",
    fg: "--petrol-contrast",
    role: "primary actions, focus, rail",
  },
  {
    bg: "--saffron",
    fg: "--saffron-contrast",
    role: "approval stamp, attention",
  },
] as const;

const statusTokens = [
  { token: "--ok", label: "Matched", icon: "✔" },
  { token: "--diff", label: "Different", icon: "≠" },
  { token: "--missing", label: "Missing", icon: "✕" },
  { token: "--review", label: "Needs review", icon: "⚠" },
] as const;

const artifactTokens = [
  { token: "--artifact-table", label: "Table" },
  { token: "--artifact-text", label: "Text" },
  { token: "--artifact-document", label: "Document" },
  { token: "--artifact-image", label: "Image" },
  { token: "--artifact-archive", label: "Archive" },
  { token: "--artifact-structured", label: "Structured" },
] as const;

const typeScale = [
  { token: "--type-xs", label: "xs · 12" },
  { token: "--type-sm", label: "sm · 14" },
  { token: "--type-base", label: "base · 16" },
  { token: "--type-lg", label: "lg · 20" },
  { token: "--type-xl", label: "xl · 25" },
  { token: "--type-2xl", label: "2xl · 31" },
  { token: "--type-3xl", label: "3xl · 39" },
] as const;

const allTokenNames = [
  ...baseTokens.map((t) => t.token),
  ...accentTokens.flatMap((t) => [t.bg, t.fg]),
  ...statusTokens.map((t) => t.token),
  ...artifactTokens.map((t) => t.token),
];

function useTokenValues(
  scopeRef: RefObject<HTMLElement | null>,
  tokens: readonly string[],
): Record<string, string> {
  const [values, setValues] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!scopeRef.current) {
      return;
    }
    const style = getComputedStyle(scopeRef.current);
    const next: Record<string, string> = {};
    for (const token of tokens) {
      next[token] = style.getPropertyValue(token).trim();
    }
    setValues(next);
  }, [scopeRef, tokens]);

  return values;
}

function Panel({ theme }: { theme: "light" | "dark" }) {
  const ref = useRef<HTMLDivElement>(null);
  const values = useTokenValues(ref, allTokenNames);

  return (
    <div
      ref={ref}
      data-theme={theme}
      className="flex-1 rounded-panel border border-line bg-bg p-6 text-ink"
    >
      <h2 className="text-start text-xl font-semibold capitalize">{theme}</h2>

      <section className="mt-4">
        <h3 className="text-start text-sm font-medium text-ink-muted">Base</h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {baseTokens.map(({ token, role }) => (
            <li
              key={token}
              className="w-40 rounded-control p-3 text-start"
              style={{ background: `var(${token})` }}
            >
              {/* A pill in the panel's own surface/ink colors, so the
                  caption stays legible even when the swatch itself IS
                  --ink or --ink-muted. */}
              <div className="inline-flex flex-col gap-0.5 rounded-sm bg-surface px-2 py-1 text-ink">
                <p className="font-mono text-xs text-ink-muted">{token}</p>
                <p className="font-mono text-xs text-ink-muted">
                  {values[token]}
                </p>
                <p className="text-sm">{role}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-4">
        <h3 className="text-start text-sm font-medium text-ink-muted">
          Accent
        </h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {accentTokens.map(({ bg, fg, role }) => (
            <li
              key={bg}
              className="w-40 rounded-control p-3 text-start text-sm"
              style={{ background: `var(${bg})`, color: `var(${fg})` }}
            >
              <p className="font-mono text-xs opacity-90">{bg}</p>
              <p className="font-mono text-xs opacity-90">{values[bg]}</p>
              <p>{role}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-4">
        <h3 className="text-start text-sm font-medium text-ink-muted">
          Status (icon + label, never color alone)
        </h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {statusTokens.map(({ token, label, icon }) => (
            <li
              key={token}
              className="flex items-center gap-2 rounded-chip border border-line bg-surface px-3 py-1 text-sm"
              style={{ color: `var(${token})` }}
            >
              <span aria-hidden="true">{icon}</span>
              <span>{label}</span>
              <span className="font-mono text-xs text-ink-muted">
                {values[token]}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-4">
        <h3 className="text-start text-sm font-medium text-ink-muted">
          Artifact types
        </h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {artifactTokens.map(({ token, label }) => (
            <li
              key={token}
              className="flex items-center gap-2 rounded-chip bg-surface px-3 py-1 text-sm text-ink"
            >
              <span
                aria-hidden="true"
                className="inline-block h-3 w-3 rounded-full"
                style={{ background: `var(${token})` }}
              />
              <span>{label}</span>
              <span className="font-mono text-xs text-ink-muted">
                {values[token]}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export function TokensPreview() {
  return (
    <main className="mx-auto max-w-5xl bg-bg p-6 text-ink">
      <h1 className="text-start text-2xl font-semibold">
        Design tokens preview
      </h1>
      <p className="mt-1 text-start text-sm text-ink-muted">
        Dev-only reference for docs/design.md §3. Not served in production.
      </p>

      <div className="mt-6 flex flex-col gap-4 md:flex-row">
        <Panel theme="light" />
        <Panel theme="dark" />
      </div>

      <section className="mt-8">
        <h2 className="text-start text-lg font-semibold">Type scale</h2>
        <ul className="mt-2 flex flex-col gap-2">
          {typeScale.map(({ token, label }) => (
            <li key={token} className="flex items-baseline gap-3 text-start">
              <span className="w-16 font-mono text-xs text-ink-muted">
                {label}
              </span>
              <span style={{ fontSize: `var(${token})` }}>
                Match orders with payments
              </span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
