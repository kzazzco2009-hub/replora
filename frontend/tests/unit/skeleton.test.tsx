import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Skeleton } from "../../src/components/ui/skeleton";

describe.each(["ltr", "rtl"] as const)("Skeleton (dir=%s)", (dir) => {
  it("renders the requested number of text lines, aria-busy", () => {
    render(
      <div dir={dir}>
        <Skeleton variant="text" count={4} aria-label="Loading summary" />
      </div>,
    );

    const root = screen.getByLabelText("Loading summary");
    expect(root.getAttribute("aria-busy")).toBe("true");
    expect(root.children.length).toBe(4);
  });

  it("renders a single card block", () => {
    render(
      <div dir={dir}>
        <Skeleton variant="card" aria-label="Loading card" />
      </div>,
    );

    expect(screen.getByLabelText("Loading card").children.length).toBe(1);
  });

  it("renders rows x columns for table-rows", () => {
    render(
      <div dir={dir}>
        <Skeleton
          variant="table-rows"
          count={3}
          columns={5}
          aria-label="Loading table"
        />
      </div>,
    );

    const root = screen.getByLabelText("Loading table");
    expect(root.children.length).toBe(3);
    expect(root.children[0]?.children.length).toBe(5);
  });

  it("stops the pulse animation under prefers-reduced-motion", () => {
    render(
      <div dir={dir}>
        <Skeleton variant="card" aria-label="Loading" />
      </div>,
    );

    const block = screen.getByLabelText("Loading").firstElementChild;
    expect(block?.className).toContain("motion-reduce:animate-none");
  });
});
