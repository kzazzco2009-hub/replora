import { fireEvent, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";
import { FileRow } from "../../src/components/features/upload/file-row";
import type { UploadItem } from "../../src/components/features/upload/use-upload-queue";
import messages from "../../messages/en.json";

function renderRow(item: UploadItem, dir: "ltr" | "rtl" = "ltr") {
  const onRemove = vi.fn();
  render(
    <div dir={dir}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <ul>
          <FileRow item={item} onRemove={onRemove} />
        </ul>
      </NextIntlClientProvider>
    </div>,
  );
  return onRemove;
}

function baseItem(overrides: Partial<UploadItem>): UploadItem {
  return {
    id: "item-1",
    file: new File([new Uint8Array(2048)], "orders.csv", {
      type: "text/csv",
    }),
    status: "uploading",
    progress: 0,
    ...overrides,
  };
}

describe.each(["ltr", "rtl"] as const)("FileRow (dir=%s)", (dir) => {
  it("shows the file name (in <bdi>) and a readable size", () => {
    renderRow(baseItem({}), dir);

    const name = screen.getByText("orders.csv");
    expect(name.closest("bdi")).not.toBeNull();
    expect(screen.getByText("2.0 KB")).toBeTruthy();
  });

  it("shows upload progress as a progressbar with the percent in text", () => {
    renderRow(baseItem({ status: "uploading", progress: 0.42 }));

    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("42");
    expect(screen.getByText(/42%/)).toBeTruthy();
  });

  it("shows the server's detected_type on ready, never by colour alone", () => {
    renderRow(baseItem({ status: "ready", detectedType: "csv" }));

    const status = screen.getByText(/Ready — detected as CSV/);
    expect(status.querySelector("svg")).not.toBeNull();
  });

  it("shows the rejection_code message on rejected", () => {
    renderRow(baseItem({ status: "rejected", rejectionCode: "ZIP_ENCRYPTED" }));

    expect(screen.getByText(/This ZIP is password-protected/)).toBeTruthy();
  });

  it("shows the client-side limit message when blocked", () => {
    renderRow(baseItem({ status: "blocked", blockedIssue: "too_many_files" }));

    expect(screen.getByText(/more files than this run allows/)).toBeTruthy();
  });

  it("shows the mapped problem message on a transport error, never raw detail", () => {
    renderRow(
      baseItem({
        status: "error",
        problem: {
          type: "about:blank",
          title: "Payload Too Large",
          status: 413,
          code: "QUOTA_EXCEEDED",
          detail: "internal: quota row 99",
          correlation_id: "01937a5e-7f00-7000-8000-00000000c0de",
        },
      }),
    );

    expect(screen.getByText(/workspace has run out of storage/)).toBeTruthy();
  });

  it("calls onRemove with the item id", () => {
    const onRemove = renderRow(baseItem({}));

    fireEvent.click(screen.getByRole("button", { name: "Remove orders.csv" }));

    expect(onRemove).toHaveBeenCalledWith("item-1");
  });
});
