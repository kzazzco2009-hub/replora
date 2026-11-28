"use client";

import { Check, Copy, type LucideIcon } from "lucide-react";
import { useState, useSyncExternalStore, type ReactNode } from "react";
import { Button } from "./button";

function noopSubscribe() {
  return () => {};
}

/** False on the server and on the client's first render, true after mount. */
function useMounted(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  );
}

export interface ErrorStateProps {
  title: string;
  description?: string;
  /** The caller's own Button, if an action applies. */
  action?: ReactNode;
  /** Decorative only; always aria-hidden. */
  icon?: LucideIcon;
  correlationId?: string;
  /** Already-translated label for the correlation id, e.g. "Reference". */
  correlationIdLabel?: string;
  /** Defaults to h2 so this fits any page outline. */
  headingLevel?: "h2" | "h3" | "h4";
  /** Shown on a copy button next to correlationId, when both are given. */
  copyLabel?: string;
  /** Replaces copyLabel after a successful copy, and is announced. */
  copiedLabel?: string;
}

/**
 * design.md §6: errors take already-translated strings and say what
 * happened. There is no `detail` prop — a problem's `detail` field must
 * never reach the UI (the error-code mapper lands in P9.6 PR 4), so there
 * is nothing here that could render it.
 */
export function ErrorState({
  title,
  description,
  action,
  icon: Icon,
  correlationId,
  correlationIdLabel,
  headingLevel = "h2",
  copyLabel,
  copiedLabel,
}: ErrorStateProps) {
  const Heading = headingLevel;
  const [copied, setCopied] = useState(false);
  // `navigator` differs between the server render and the client's first
  // paint, so the clipboard check only runs once `mounted` flips to true
  // (after hydration), never inline during the first render.
  const mounted = useMounted();
  const canCopy =
    mounted && typeof navigator !== "undefined" && !!navigator.clipboard;

  async function handleCopy() {
    if (!correlationId) return;
    await navigator.clipboard.writeText(correlationId);
    setCopied(true);
  }

  const showCopyButton =
    canCopy && correlationId !== undefined && copyLabel !== undefined;

  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-3 px-6 py-12 text-start"
    >
      {Icon ? (
        <Icon
          aria-hidden="true"
          size={32}
          strokeWidth={1.75}
          className="text-missing"
        />
      ) : null}
      <Heading className="text-lg font-semibold text-ink">{title}</Heading>
      {description ? (
        <p className="text-sm text-ink-muted">{description}</p>
      ) : null}
      {action}
      {correlationId ? (
        <p className="text-xs text-ink-muted">
          {correlationIdLabel}{" "}
          <span className="select-all font-mono">{correlationId}</span>
        </p>
      ) : null}
      {showCopyButton ? (
        <Button variant="secondary" onClick={handleCopy}>
          {copied ? (
            <Check aria-hidden="true" size={16} strokeWidth={1.75} />
          ) : (
            <Copy aria-hidden="true" size={16} strokeWidth={1.75} />
          )}
          {copied ? copiedLabel : copyLabel}
        </Button>
      ) : null}
      {showCopyButton ? (
        <span role="status" className="sr-only">
          {copied ? copiedLabel : ""}
        </span>
      ) : null}
    </div>
  );
}
