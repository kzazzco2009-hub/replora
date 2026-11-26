import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "../../src/components/ui/badge";

describe.each(["ltr", "rtl"] as const)("Badge (dir=%s)", (dir) => {
  it("renders its content as text", () => {
    render(
      <div dir={dir}>
        <Badge>Owner</Badge>
      </div>,
    );

    expect(screen.getByText("Owner").tagName).toBe("SPAN");
  });

  it("merges a caller-supplied className instead of replacing the base styles", () => {
    render(
      <div dir={dir}>
        <Badge className="extra-class">Admin</Badge>
      </div>,
    );

    const badge = screen.getByText("Admin");
    expect(badge.className).toContain("extra-class");
    expect(badge.className).toContain("rounded-chip");
  });
});
