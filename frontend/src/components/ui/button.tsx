import type { ComponentProps } from "react";

export type ButtonVariant = "primary" | "secondary" | "stamp";

/** design.md §3: petrol for primary actions, saffron reserved for approval ("stamp"). */
const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-petrol text-petrol-contrast hover:opacity-90",
  secondary: "border border-line text-ink hover:bg-surface",
  stamp: "bg-saffron text-saffron-contrast hover:opacity-90",
};

export interface ButtonProps extends ComponentProps<"button"> {
  variant?: ButtonVariant;
}

/** Touch target stays >= 44px tall (design.md §4) regardless of variant. */
export function Button({
  variant = "primary",
  type = "button",
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      {...props}
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-control px-4 text-sm font-medium duration-[var(--duration-fast)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT_CLASSES[variant]} ${className}`}
    />
  );
}
