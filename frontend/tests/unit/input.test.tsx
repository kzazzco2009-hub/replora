import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Input } from "../../src/components/ui/input";

describe.each(["ltr", "rtl"] as const)("Input (dir=%s)", (dir) => {
  it("connects the visible label to the field (no placeholder-as-label)", () => {
    render(
      <div dir={dir}>
        <Input label="Workspace name" />
      </div>,
    );

    const field = screen.getByLabelText("Workspace name");
    expect(field.tagName).toBe("INPUT");
  });

  it("shows the error as an icon plus text, linked by aria-describedby", () => {
    render(
      <div dir={dir}>
        <Input label="Email" error="Enter a valid email address." />
      </div>,
    );

    const field = screen.getByLabelText("Email");
    const describedBy = field.getAttribute("aria-describedby");
    expect(describedBy).toBeTruthy();

    const message = document.getElementById(describedBy as string);
    expect(message?.textContent).toContain("Enter a valid email address.");
    // icon + text, never colour alone (design.md §3)
    expect(message?.querySelector("svg")).not.toBeNull();
    expect(field.getAttribute("aria-invalid")).toBe("true");
  });

  it("has no aria-describedby or aria-invalid when there is no error", () => {
    render(
      <div dir={dir}>
        <Input label="Email" />
      </div>,
    );

    const field = screen.getByLabelText("Email");
    expect(field.getAttribute("aria-describedby")).toBeNull();
    expect(field.getAttribute("aria-invalid")).toBeNull();
  });
});
