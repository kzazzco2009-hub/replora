"use client";

import * as RadixDialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

export interface SheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The sheet's accessible name; always rendered visibly (design.md §9). */
  title: string;
  closeLabel: string;
  description?: string;
  children: ReactNode;
}

/**
 * A side panel that slides in from the inline-end edge (right in EN/LTR,
 * left in AR/RTL). The slide direction is physical (`translate-x`), so it
 * is the one place in this component that needs explicit `ltr:`/`rtl:`
 * variants rather than a logical utility.
 */
export function Sheet({
  open,
  onOpenChange,
  title,
  closeLabel,
  description,
  children,
}: SheetProps) {
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        {/* Scrim stays the same dark colour in both themes: it darkens
            whatever is behind it, so it must not flip with --ink. */}
        <RadixDialog.Overlay className="fixed inset-0 bg-black/50" />
        <RadixDialog.Content
          aria-describedby={undefined}
          className="fixed inset-y-0 end-0 flex w-[90vw] max-w-sm flex-col gap-3 overflow-y-auto bg-surface-raised p-6 text-ink outline-none transition-transform duration-[var(--duration-base)] ltr:data-[state=closed]:translate-x-full rtl:data-[state=closed]:-translate-x-full data-[state=open]:translate-x-0"
        >
          <div className="flex items-start justify-between gap-4">
            <RadixDialog.Title className="text-lg font-semibold">
              {title}
            </RadixDialog.Title>
            <RadixDialog.Close
              aria-label={closeLabel}
              className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-control focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
            >
              <X aria-hidden="true" size={20} strokeWidth={1.75} />
            </RadixDialog.Close>
          </div>
          {description ? (
            <RadixDialog.Description className="text-sm text-ink-muted">
              {description}
            </RadixDialog.Description>
          ) : null}
          {children}
        </RadixDialog.Content>
      </RadixDialog.Portal>
    </RadixDialog.Root>
  );
}
