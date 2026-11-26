import { AlertCircle } from "lucide-react";
import { useId } from "react";
import type { ComponentProps } from "react";

export interface InputProps extends Omit<ComponentProps<"input">, "id"> {
  /** Always visible; design.md §9 bans placeholder-as-label. */
  label: string;
  error?: string;
}

/** design.md §3/§9: error is icon + text, never colour alone, and linked with aria-describedby. */
export function Input({ label, error, className = "", ...props }: InputProps) {
  const id = useId();
  const errorId = `${id}-error`;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...props}
        className={`min-h-11 rounded-control border bg-surface px-3 text-base text-ink outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring ${error ? "border-missing" : "border-line"} ${className}`}
      />
      {error ? (
        <p
          id={errorId}
          className="flex items-center gap-1 text-sm text-missing"
        >
          <AlertCircle aria-hidden="true" size={16} strokeWidth={1.75} />
          {error}
        </p>
      ) : null}
    </div>
  );
}
