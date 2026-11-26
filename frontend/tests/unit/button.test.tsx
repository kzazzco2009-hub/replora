import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Button } from "../../src/components/ui/button";

describe.each(["ltr", "rtl"] as const)("Button (dir=%s)", (dir) => {
  it("renders its label and responds to a click", () => {
    const onClick = vi.fn();
    render(
      <div dir={dir}>
        <Button onClick={onClick}>Approve and run</Button>
      </div>,
    );

    const button = screen.getByRole("button", { name: "Approve and run" });
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("does not fire onClick while disabled", () => {
    const onClick = vi.fn();
    render(
      <div dir={dir}>
        <Button onClick={onClick} disabled>
          Approve and run
        </Button>
      </div>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Approve and run" }));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("defaults to type=button, so it never submits a surrounding form by accident", () => {
    render(
      <div dir={dir}>
        <Button>Save</Button>
      </div>,
    );

    expect(
      screen.getByRole("button", { name: "Save" }).getAttribute("type"),
    ).toBe("button");
  });
});
