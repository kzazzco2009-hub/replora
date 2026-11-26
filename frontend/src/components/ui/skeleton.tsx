export type SkeletonVariant = "text" | "card" | "table-rows";

export interface SkeletonProps {
  variant: SkeletonVariant;
  /** Number of lines ("text") or rows ("table-rows"); ignored for "card". */
  count?: number;
  /** Columns per row, only for "table-rows". */
  columns?: number;
  "aria-label"?: string;
}

const PULSE =
  "animate-pulse motion-reduce:animate-none rounded-control bg-line";

/** design.md §4/§8: no shimmer under prefers-reduced-motion. */
export function Skeleton({
  variant,
  count = 3,
  columns = 4,
  "aria-label": ariaLabel,
}: SkeletonProps) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label={ariaLabel}
      className="flex flex-col gap-2"
    >
      {variant === "text" &&
        Array.from({ length: count }, (_, line) => (
          <div
            key={line}
            className={`h-4 ${PULSE}`}
            style={{ width: line === count - 1 ? "60%" : "100%" }}
          />
        ))}
      {variant === "card" && <div className={`h-32 w-full ${PULSE}`} />}
      {variant === "table-rows" &&
        Array.from({ length: count }, (_, row) => (
          <div key={row} className="flex gap-2">
            {Array.from({ length: columns }, (_, col) => (
              <div key={col} className={`h-4 flex-1 ${PULSE}`} />
            ))}
          </div>
        ))}
    </div>
  );
}
