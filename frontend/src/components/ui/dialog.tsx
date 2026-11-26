"use client";

import * as RadixDialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

export interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** The dialog's accessible name; always rendered visibly (design.md §9). */
  title: string;
  closeLabel: string;
  description?: string;
  children: ReactNode;
}

/** design.md §3: dialogs use radius-dialog and surface-raised elevation. */
export function Dialog({
  open,
  onOpenChange,
  title,
  closeLabel,
  description,
  children,
}: DialogProps) {
  return (
    <RadixDialog.Root open={open} onOpenChange={onOpenChange}>
      <RadixDialog.Portal>
        {/* Scrim stays the same dark colour in both themes: it darkens
            whatever is behind it, so it must not flip with --ink. */}
        <RadixDialog.Overlay className="fixed inset-0 bg-black/50" />
        <RadixDialog.Content
          className="fixed inset-0 m-auto flex max-h-[85vh] w-[90vw] max-w-md flex-col gap-3 overflow-y-auto rounded-dialog bg-surface-raised p-6 text-ink outline-none"
          style={{ height: "fit-content" }}
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
