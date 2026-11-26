import { render, screen } from "@testing-library/react";
import { Inbox } from "lucide-react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "../../src/components/ui/empty-state";

describe.each(["ltr", "rtl"] as const)("EmptyState (dir=%s)", (dir) => {
  it("renders the title, description and action", () => {
    render(
      <div dir={dir}>
        <EmptyState
          title="No runs yet"
          description="Upload two files to compare them."
          action={<button type="button">Start a new run</button>}
        />
      </div>,
    );

    expect(screen.getByRole("heading", { name: "No runs yet" })).toBeTruthy();
    expect(screen.getByText("Upload two files to compare them.")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Start a new run" }),
    ).toBeTruthy();
  });

  it("defaults to an h2 heading", () => {
    render(
      <div dir={dir}>
        <EmptyState title="No runs yet" />
      </div>,
    );

    expect(
      screen.getByRole("heading", { level: 2, name: "No runs yet" }),
    ).toBeTruthy();
  });

  it("renders the given heading level", () => {
    render(
      <div dir={dir}>
        <EmptyState title="No runs yet" headingLevel="h3" />
      </div>,
    );

    expect(
      screen.getByRole("heading", { level: 3, name: "No runs yet" }),
    ).toBeTruthy();
  });

  it("renders no action button when none is given", () => {
    render(
      <div dir={dir}>
        <EmptyState title="No runs yet" />
      </div>,
    );

    expect(screen.queryByRole("button")).toBeNull();
  });

  it("renders a decorative, aria-hidden icon when given", () => {
    render(
      <div dir={dir}>
        <EmptyState title="No runs yet" icon={Inbox} />
      </div>,
    );

    expect(document.querySelector("svg")?.getAttribute("aria-hidden")).toBe(
      "true",
    );
  });
});
