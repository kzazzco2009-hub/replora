import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Skeleton } from "../../src/components/ui/skeleton";

describe.each(["ltr", "rtl"] as const)("Skeleton (dir=%s)", (dir) => {
  it("has role=status so its label is announced, plus aria-busy", () => {
    render(
      <div dir={dir}>
        <Skeleton variant="text" aria-label="Loading summary" />
      </div>,
    );

    const root = screen.getByRole("status", { name: "Loading summary" });
    expect(root.getAttribute("aria-busy")).toBe("true");
  });

  it("renders the requested number of text lines", () => {
    render(
      <div dir={dir}>
        <Skeleton variant="text" count={4} aria-label="Loading summary" />
      </div>,
    );

    expect(
      screen.getByRole("status", { name: "Loading summary" }).children.length,
    ).toBe(4);
  });

  it("renders a single card block", () => {
    render(
      <div dir={dir}>
        <Skeleton variant="card" aria-label="Loading card" />
      </div>,
    );

    expect(
      screen.getByRole("status", { name: "Loading card" }).children.length,
    ).toBe(1);
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

    const root = screen.getByRole("status", { name: "Loading table" });
    expect(root.children.length).toBe(3);
    expect(root.children[0]?.children.length).toBe(5);
  });

  it("stops the pulse animation under prefers-reduced-motion", () => {
    render(
      <div dir={dir}>
        <Skeleton variant="card" aria-label="Loading" />
      </div>,
    );

    const block = screen.getByRole("status", {
      name: "Loading",
    }).firstElementChild;
    expect(block?.className).toContain("motion-reduce:animate-none");
  });
});
