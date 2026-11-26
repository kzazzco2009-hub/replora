import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Select, type SelectProps } from "../../src/components/ui/select";
import { installSelectJsdomPolyfills } from "./select-jsdom-polyfills";

const OPTIONS = [
  { value: "sum", label: "Sum" },
  { value: "count", label: "Count" },
  { value: "avg", label: "Average", disabled: true },
];

describe.each(["ltr", "rtl"] as const)("Select (dir=%s)", (dir) => {
  let restorePolyfills: () => void;

  // RadixSelect.Portal renders into document.body, outside the <div dir>
  // wrapper below, so the document's own dir must be set for the rtl case
  // to really exercise RTL; the component's own `dir` prop drives Radix's
  // keyboard-direction and popper-alignment logic.
  beforeEach(() => {
    document.documentElement.dir = dir;
    restorePolyfills = installSelectJsdomPolyfills();
  });

  afterEach(() => {
    document.documentElement.dir = "";
    restorePolyfills();
  });

  function renderSelect(overrides: Partial<SelectProps> = {}) {
    const onValueChange = overrides.onValueChange ?? vi.fn();
    render(
      <div dir={dir}>
        <Select
          label="Aggregation"
          options={OPTIONS}
          dir={dir}
          onValueChange={onValueChange}
          {...overrides}
        />
      </div>,
    );
    return onValueChange;
  }

  it("sets the document dir for this case", () => {
    expect(document.documentElement.dir).toBe(dir);
  });

  it("connects the visible label to the trigger (no placeholder-as-label)", () => {
    renderSelect({ placeholder: "Choose one" });

    const trigger = screen.getByLabelText("Aggregation");
    expect(trigger.tagName).toBe("BUTTON");
    expect(screen.getByText("Choose one")).toBeTruthy();
  });

  it("has a >=44px trigger", () => {
    renderSelect();

    expect(screen.getByLabelText("Aggregation").className).toContain(
      "min-h-11",
    );
  });

  it("opens on click and lists its options", () => {
    renderSelect();

    fireEvent.click(screen.getByLabelText("Aggregation"));

    expect(screen.getByRole("listbox")).toBeTruthy();
    expect(screen.getByRole("option", { name: "Sum" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Count" })).toBeTruthy();
  });

  it("selects an option on click and calls onValueChange", () => {
    const onValueChange = renderSelect();

    fireEvent.click(screen.getByLabelText("Aggregation"));
    fireEvent.click(screen.getByRole("option", { name: "Count" }));

    expect(onValueChange).toHaveBeenCalledWith("count");
  });

  it("marks a disabled option as unselectable", () => {
    renderSelect();

    fireEvent.click(screen.getByLabelText("Aggregation"));

    expect(
      screen
        .getByRole("option", { name: "Average" })
        .getAttribute("aria-disabled"),
    ).toBe("true");
  });

  it("disables the trigger", () => {
    renderSelect({ disabled: true });

    const trigger = screen.getByLabelText("Aggregation") as HTMLButtonElement;
    expect(trigger.disabled).toBe(true);
  });

  it("shows the error as an icon plus text, merged into a caller aria-describedby", () => {
    renderSelect({
      error: "Pick an aggregation.",
      "aria-describedby": "hint-id",
    });

    const trigger = screen.getByLabelText("Aggregation");
    const describedBy = (trigger.getAttribute("aria-describedby") ?? "").split(
      " ",
    );
    expect(describedBy).toContain("hint-id");

    const errorId = describedBy.find((part) => part !== "hint-id");
    const message = document.getElementById(errorId as string);
    expect(message?.textContent).toContain("Pick an aggregation.");
    expect(message?.querySelector("svg")).not.toBeNull();
    expect(trigger.getAttribute("aria-invalid")).toBe("true");
  });

  it("has no aria-describedby or aria-invalid when there is no error", () => {
    renderSelect();

    const trigger = screen.getByLabelText("Aggregation");
    expect(trigger.getAttribute("aria-describedby")).toBeNull();
    expect(trigger.getAttribute("aria-invalid")).toBeNull();
  });
});
