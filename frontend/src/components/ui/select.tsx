"use client";

import * as RadixSelect from "@radix-ui/react-select";
import { AlertCircle, Check, ChevronDown } from "lucide-react";
import { useId } from "react";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps {
  /** Always visible; design.md §9 bans placeholder-as-label. */
  label: string;
  options: SelectOption[];
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  name?: string;
  dir?: "ltr" | "rtl";
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  "aria-describedby"?: string;
}

/** design.md §3/§9: error is icon + text, never colour alone, and linked with aria-describedby. */
export function Select({
  label,
  options,
  placeholder,
  error,
  disabled,
  required,
  name,
  dir,
  value,
  defaultValue,
  onValueChange,
  "aria-describedby": ariaDescribedBy,
}: SelectProps) {
  const id = useId();
  const errorId = `${id}-error`;
  const describedBy =
    [ariaDescribedBy, error ? errorId : null].filter(Boolean).join(" ") ||
    undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
      </label>
      <RadixSelect.Root
        name={name}
        dir={dir}
        value={value}
        defaultValue={defaultValue}
        onValueChange={onValueChange}
        disabled={disabled}
        required={required}
      >
        <RadixSelect.Trigger
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={`flex min-h-11 items-center justify-between gap-2 rounded-control border bg-surface px-3 text-start text-base text-ink outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring disabled:cursor-not-allowed disabled:opacity-50 ${error ? "border-missing" : "border-line"}`}
        >
          <RadixSelect.Value placeholder={placeholder} />
          <RadixSelect.Icon>
            <ChevronDown aria-hidden="true" size={20} strokeWidth={1.75} />
          </RadixSelect.Icon>
        </RadixSelect.Trigger>
        <RadixSelect.Portal>
          <RadixSelect.Content
            position="popper"
            align="start"
            sideOffset={4}
            className="z-50 overflow-hidden rounded-control border border-line bg-surface-raised text-ink shadow-lg"
          >
            <RadixSelect.ScrollUpButton className="flex items-center justify-center py-1">
              <ChevronDown
                aria-hidden="true"
                size={16}
                strokeWidth={1.75}
                className="rotate-180"
              />
            </RadixSelect.ScrollUpButton>
            <RadixSelect.Viewport className="p-1">
              {options.map((option) => (
                <RadixSelect.Item
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                  className="flex min-h-11 items-center gap-2 rounded-control px-3 text-sm outline-none data-[highlighted]:bg-surface data-[disabled]:cursor-not-allowed data-[disabled]:opacity-50"
                >
                  <RadixSelect.ItemText>{option.label}</RadixSelect.ItemText>
                  <RadixSelect.ItemIndicator className="ms-auto">
                    <Check aria-hidden="true" size={16} strokeWidth={1.75} />
                  </RadixSelect.ItemIndicator>
                </RadixSelect.Item>
              ))}
            </RadixSelect.Viewport>
            <RadixSelect.ScrollDownButton className="flex items-center justify-center py-1">
              <ChevronDown aria-hidden="true" size={16} strokeWidth={1.75} />
            </RadixSelect.ScrollDownButton>
          </RadixSelect.Content>
        </RadixSelect.Portal>
      </RadixSelect.Root>
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
