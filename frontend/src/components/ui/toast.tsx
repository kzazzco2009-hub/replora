"use client";

import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";
import { Toaster as SonnerToaster, toast } from "sonner";

export type ToastVariant = "success" | "error" | "info";

/** design.md §6: icon + text, never colour alone. */
const VARIANT_ICON = {
  success: CheckCircle2,
  error: AlertTriangle,
  info: Info,
} as const;

export type ShowToastOptions =
  | {
      variant: "error";
      title: string;
      description?: string;
      closeLabel: string;
    }
  | { variant: "success" | "info"; title: string; description?: string };

/**
 * Shows one toast. Errors never auto-dismiss and get their own close
 * button, since the user may need time to read and act on them.
 */
export function showToast(options: ShowToastOptions) {
  const Icon = VARIANT_ICON[options.variant];

  toast.custom(
    (id) => (
      <div
        role={options.variant === "error" ? "alert" : "status"}
        className="flex items-start gap-2 rounded-panel border border-line bg-surface-raised p-3 text-sm text-ink shadow-lg"
      >
        <Icon
          aria-hidden="true"
          size={20}
          strokeWidth={1.75}
          className="mt-0.5 shrink-0"
        />
        <div className="flex-1">
          <p className="font-medium">{options.title}</p>
          {options.description ? (
            <p className="text-ink-muted">{options.description}</p>
          ) : null}
        </div>
        {options.variant === "error" ? (
          <button
            type="button"
            aria-label={options.closeLabel}
            onClick={() => toast.dismiss(id)}
            className="inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-control focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          >
            <X aria-hidden="true" size={20} strokeWidth={1.75} />
          </button>
        ) : null}
      </div>
    ),
    { duration: options.variant === "error" ? Infinity : 4000 },
  );
}

/** Mounted once near the app root. Position follows the inline-end corner. */
export function Toaster({ dir }: { dir: "ltr" | "rtl" }) {
  return (
    <SonnerToaster
      dir={dir}
      position={dir === "rtl" ? "top-left" : "top-right"}
    />
  );
}
