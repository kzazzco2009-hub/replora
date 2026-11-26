import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { customMock, dismissMock } = vi.hoisted(() => ({
  customMock: vi.fn(),
  dismissMock: vi.fn(),
}));

// sonner's real Toaster mounts a toast store driven by requestAnimationFrame,
// which is irrelevant to what this file owns: the duration/role/close-button
// contract in showToast, and the dir -> position mapping in Toaster. Mocked
// the way tests/setup.ts already mocks next/font/google for the same reason.
vi.mock("sonner", () => ({
  toast: { custom: customMock, dismiss: dismissMock },
  Toaster: ({ dir, position }: { dir: string; position: string }) => (
    <div data-testid="toaster" data-dir={dir} data-position={position} />
  ),
}));

const { showToast, Toaster } = await import("../../src/components/ui/toast");

describe.each(["ltr", "rtl"] as const)("Toast (dir=%s)", (dir) => {
  // sonner's real Toaster renders via a portal into document.body, outside
  // any <div dir> wrapper, so the document's own dir must be set for the
  // rtl case to really exercise RTL.
  beforeEach(() => {
    document.documentElement.dir = dir;
  });

  afterEach(() => {
    document.documentElement.dir = "";
  });

  it("shows an icon and text for a success toast, with no close button and a finite duration", () => {
    showToast({ variant: "success", title: "Run started" });

    const [renderToast, options] = customMock.mock.calls.at(-1)!;
    expect(options.duration).toBe(4000);

    render(<div dir={dir}>{renderToast(1)}</div>);
    const status = screen.getByRole("status");
    expect(status.querySelector("svg")).not.toBeNull();
    expect(screen.getByText("Run started")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("shows role=alert, an icon, text and a >=44px close button for an error toast, with no auto-dismiss", () => {
    showToast({
      variant: "error",
      title: "Run failed",
      closeLabel: "Close",
    });

    const [renderToast, options] = customMock.mock.calls.at(-1)!;
    expect(options.duration).toBe(Infinity);

    render(<div dir={dir}>{renderToast(2)}</div>);
    const alert = screen.getByRole("alert");
    expect(alert.querySelector("svg")).not.toBeNull();
    expect(screen.getByText("Run failed")).toBeTruthy();

    const closeButton = screen.getByRole("button", { name: "Close" });
    expect(closeButton.className).toContain("min-h-11");
    expect(closeButton.className).toContain("min-w-11");

    fireEvent.click(closeButton);
    expect(dismissMock).toHaveBeenCalledWith(2);
  });
});

describe.each(["ltr", "rtl"] as const)("Toaster (dir=%s)", (dir) => {
  beforeEach(() => {
    document.documentElement.dir = dir;
  });

  afterEach(() => {
    document.documentElement.dir = "";
  });

  it("positions the stack at the inline-end top corner for this direction", () => {
    render(<Toaster dir={dir} />);

    const stack = screen.getByTestId("toaster");
    expect(stack.getAttribute("data-dir")).toBe(dir);
    expect(stack.getAttribute("data-position")).toBe(
      dir === "rtl" ? "top-left" : "top-right",
    );
  });
});
