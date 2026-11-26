import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

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
}: ErrorStateProps) {
  const Heading = headingLevel;

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
    </div>
  );
}
