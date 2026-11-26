import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export interface EmptyStateProps {
  title: string;
  description?: string;
  /** The caller's own Button, if an action applies. */
  action?: ReactNode;
  /** Decorative only; always aria-hidden. */
  icon?: LucideIcon;
  /** Defaults to h2 so this fits any page outline. */
  headingLevel?: "h2" | "h3" | "h4";
}

/** design.md §4: the only centered content on the page is an empty state. */
export function EmptyState({
  title,
  description,
  action,
  icon: Icon,
  headingLevel = "h2",
}: EmptyStateProps) {
  const Heading = headingLevel;

  return (
    <div className="flex flex-col items-center gap-3 px-6 py-12 text-center">
      {Icon ? (
        <Icon
          aria-hidden="true"
          size={32}
          strokeWidth={1.75}
          className="text-ink-muted"
        />
      ) : null}
      <Heading className="text-lg font-semibold text-ink">{title}</Heading>
      {description ? (
        <p className="text-sm text-ink-muted">{description}</p>
      ) : null}
      {action}
    </div>
  );
}
