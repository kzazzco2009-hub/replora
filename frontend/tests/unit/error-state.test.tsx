import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AlertTriangle } from "lucide-react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ErrorState } from "../../src/components/ui/error-state";

function mockClipboard() {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", {
    value: { writeText },
    configurable: true,
  });
  return writeText;
}

afterEach(() => {
  Reflect.deleteProperty(navigator, "clipboard");
});

describe.each(["ltr", "rtl"] as const)("ErrorState (dir=%s)", (dir) => {
  it("renders the title, description and action with role=alert", () => {
    render(
      <div dir={dir}>
        <ErrorState
          title="This file could not be read."
          description="Upload the original CSV export."
          action={<button type="button">Try again</button>}
        />
      </div>,
    );

    expect(screen.getByRole("alert")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "This file could not be read." }),
    ).toBeTruthy();
    expect(screen.getByText("Upload the original CSV export.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
  });

  it("defaults to an h2 heading and accepts a different level", () => {
    render(
      <div dir={dir}>
        <ErrorState title="Error" headingLevel="h4" />
      </div>,
    );

    expect(
      screen.getByRole("heading", { level: 4, name: "Error" }),
    ).toBeTruthy();
  });

  it("shows the correlation id with its label, as selectable monospace text", () => {
    render(
      <div dir={dir}>
        <ErrorState
          title="Error"
          correlationId="01J000000000000000000000"
          correlationIdLabel="Reference"
        />
      </div>,
    );

    expect(screen.getByText("Reference")).toBeTruthy();
    const idText = screen.getByText("01J000000000000000000000");
    expect(idText.className).toContain("select-all");
    expect(idText.className).toContain("font-mono");
  });

  it("shows no correlation id line when none is given", () => {
    render(
      <div dir={dir}>
        <ErrorState title="Error" />
      </div>,
    );

    expect(screen.queryByText("Reference")).toBeNull();
  });

  it("renders a decorative, aria-hidden icon when given", () => {
    render(
      <div dir={dir}>
        <ErrorState title="Error" icon={AlertTriangle} />
      </div>,
    );

    expect(document.querySelector("svg")?.getAttribute("aria-hidden")).toBe(
      "true",
    );
  });

  it("has no detail prop at the type level, and never renders an unknown extra field", () => {
    render(
      <div dir={dir}>
        {/* @ts-expect-error ErrorStateProps has no `detail` field by design — a problem's detail must never reach the UI. */}
        <ErrorState title="Error" detail="super secret stack trace" />
      </div>,
    );

    expect(screen.queryByText(/super secret stack trace/)).toBeNull();
  });

  it("copies the correlation id and swaps to the copied label, announced in a status region", async () => {
    mockClipboard();
    render(
      <div dir={dir}>
        <ErrorState
          title="Error"
          correlationId="01J000000000000000000000"
          correlationIdLabel="Reference"
          copyLabel="Copy"
          copiedLabel="Copied"
        />
      </div>,
    );

    const button = await screen.findByRole("button", { name: "Copy" });
    expect(button.className).toMatch(/min-h-11/);
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Copied" })).toBeTruthy();
    });
    expect(screen.getByRole("status").textContent).toBe("Copied");
  });

  it("renders no copy button without a copyLabel, even with a correlation id", async () => {
    mockClipboard();
    render(
      <div dir={dir}>
        <ErrorState
          title="Error"
          correlationId="01J000000000000000000000"
          correlationIdLabel="Reference"
        />
      </div>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("button")).toBeNull();
    });
  });

  it("renders no copy button when navigator.clipboard is unavailable", async () => {
    render(
      <div dir={dir}>
        <ErrorState
          title="Error"
          correlationId="01J000000000000000000000"
          correlationIdLabel="Reference"
          copyLabel="Copy"
          copiedLabel="Copied"
        />
      </div>,
    );

    await waitFor(() => {
      expect(screen.queryByRole("button")).toBeNull();
    });
    expect(screen.getByText("01J000000000000000000000")).toBeTruthy();
  });
});
