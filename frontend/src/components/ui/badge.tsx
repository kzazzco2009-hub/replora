import type { ComponentProps } from "react";

/** Neutral pill (role labels, counts). design.md §3: radius-chip is fully round. */
export function Badge({ className = "", ...props }: ComponentProps<"span">) {
  return (
    <span
      {...props}
      className={`inline-flex items-center gap-1 rounded-chip border border-line bg-surface px-2.5 py-0.5 text-xs font-medium text-ink-muted ${className}`}
    />
  );
}
