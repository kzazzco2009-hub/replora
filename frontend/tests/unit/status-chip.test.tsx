import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  StatusChip,
  type StatusChipStatus,
} from "../../src/components/ui/status-chip";

const ALL_STATUSES: StatusChipStatus[] = [
  "matched",
  "value_diff",
  "missing_left",
  "missing_right",
  "DRAFT",
  "VALIDATED",
  "AWAITING_APPROVAL",
  "QUEUED",
  "RUNNING",
  "NEEDS_REVIEW",
  "SUCCEEDED",
  "PARTIAL",
  "FAILED",
  "CANCEL_REQUESTED",
  "CANCELLED",
  "EXPIRED",
];

describe.each(["ltr", "rtl"] as const)("StatusChip (dir=%s)", (dir) => {
  it.each(ALL_STATUSES)(
    "renders an icon and the given label for %s (never colour alone)",
    (status) => {
      render(
        <div dir={dir}>
          <StatusChip status={status} label={`Label for ${status}`} />
        </div>,
      );

      const text = screen.getByText(`Label for ${status}`);
      expect(text.closest("span")?.querySelector("svg")).not.toBeNull();
    },
  );

  it("uses the ok colour for matched/succeeded", () => {
    render(
      <div dir={dir}>
        <StatusChip status="matched" label="Matched" />
      </div>,
    );

    expect(screen.getByText("Matched").closest("span")?.className).toContain(
      "text-ok",
    );
  });

  it("uses the missing colour for failed", () => {
    render(
      <div dir={dir}>
        <StatusChip status="FAILED" label="Failed" />
      </div>,
    );

    expect(screen.getByText("Failed").closest("span")?.className).toContain(
      "text-missing",
    );
  });

  it("uses saffron for awaiting approval", () => {
    render(
      <div dir={dir}>
        <StatusChip status="AWAITING_APPROVAL" label="Awaiting approval" />
      </div>,
    );

    expect(
      screen.getByText("Awaiting approval").closest("span")?.className,
    ).toContain("text-saffron");
  });

  it("uses muted for a non-terminal lifecycle state with no defined colour", () => {
    render(
      <div dir={dir}>
        <StatusChip status="QUEUED" label="Queued" />
      </div>,
    );

    expect(screen.getByText("Queued").closest("span")?.className).toContain(
      "text-ink-muted",
    );
  });
});
