"use client";

import * as RadixTabs from "@radix-ui/react-tabs";
import type { ReactNode } from "react";

export interface TabItem {
  value: string;
  label: ReactNode;
  content: ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  /** The tab list's accessible name (aria-label); the tabs have no separate visible heading. */
  label: string;
  tabs: TabItem[];
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  dir?: "ltr" | "rtl";
}

/**
 * design.md §3: the active tab is never shown by colour alone — a petrol
 * bottom border plus a heavier weight mark it, and neither is
 * direction-specific (the border sits on the block axis, not inline).
 */
export function Tabs({
  label,
  tabs,
  value,
  defaultValue,
  onValueChange,
  dir,
}: TabsProps) {
  return (
    <RadixTabs.Root
      value={value}
      defaultValue={defaultValue ?? tabs[0]?.value}
      onValueChange={onValueChange}
      dir={dir}
    >
      <RadixTabs.List aria-label={label} className="flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <RadixTabs.Trigger
            key={tab.value}
            value={tab.value}
            disabled={tab.disabled}
            className="inline-flex min-h-11 min-w-11 items-center justify-center whitespace-nowrap border-b-2 border-transparent px-4 text-sm font-medium text-ink-muted outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring disabled:cursor-not-allowed disabled:opacity-50 data-[state=active]:border-petrol data-[state=active]:font-semibold data-[state=active]:text-ink"
          >
            {tab.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {tabs.map((tab) => (
        <RadixTabs.Content key={tab.value} value={tab.value} className="pt-4">
          {tab.content}
        </RadixTabs.Content>
      ))}
    </RadixTabs.Root>
  );
}
