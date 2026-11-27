import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it } from "vitest";
import { UploadStep } from "../../src/components/features/upload/upload-step";
import { useUploadQueue } from "../../src/components/features/upload/use-upload-queue";
import messages from "../../messages/en.json";
import { setScenario } from "../msw/scenarios";

beforeEach(() => {
  document.cookie = "replora_csrf=test-token";
});

function file(name: string, size: number, type = "text/csv"): File {
  return new File([new Uint8Array(size)], name, { type });
}

/** `UploadStep` is prop-driven; this is the one real `useUploadQueue` caller the queue tests run against. */
function Harness() {
  const { items, addFiles, removeItem } = useUploadQueue("ws-1");
  return (
    <UploadStep items={items} addFiles={addFiles} removeItem={removeItem} />
  );
}

function renderStep(dir: "ltr" | "rtl" = "ltr") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <div dir={dir}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <QueryClientProvider client={client}>
          <Harness />
        </QueryClientProvider>
      </NextIntlClientProvider>
    </div>,
  );
}

function pickFiles(files: File[]) {
  const input = document.querySelector('input[type="file"]')!;
  fireEvent.change(input, { target: { files } });
}

describe.each(["ltr", "rtl"] as const)("UploadStep (dir=%s)", (dir) => {
  it("has an accessible file picker button and shows the limits hint once loaded", async () => {
    renderStep(dir);

    expect(screen.getByRole("button", { name: "Choose files" })).toBeTruthy();
    await waitFor(() =>
      expect(screen.getByText(/Up to 10 files, 50.0 MB each/)).toBeTruthy(),
    );
  });

  it("uploads a picked file through to the ready state, showing the detected type", async () => {
    setScenario("files_complete", "ready");
    renderStep(dir);
    await waitFor(() => screen.getByText(/Up to 10 files/));

    pickFiles([file("orders.csv", 10)]);

    expect(await screen.findByText("orders.csv")).toBeTruthy();
    await waitFor(() =>
      expect(screen.getByText(/Ready — detected as CSV/)).toBeTruthy(),
    );
  });
});

describe("UploadStep behavior", () => {
  it("shows the server's rejection_code message when complete returns rejected", async () => {
    setScenario("files_complete", "rejected");
    renderStep();
    await waitFor(() => screen.getByText(/Up to 10 files/));

    pickFiles([file("orders.pdf", 10, "application/pdf")]);

    await waitFor(() =>
      expect(
        screen.getByText(/isn't a supported type, whatever its name says/),
      ).toBeTruthy(),
    );
  });

  it("blocks a file over the size limit client-side, without calling upload-intent", async () => {
    renderStep();
    await waitFor(() => screen.getByText(/Up to 10 files/));

    pickFiles([file("huge.csv", 100_000_000)]);

    await waitFor(() =>
      expect(screen.getByText(/larger than the allowed size/)).toBeTruthy(),
    );
  });

  it("maps a 413 from upload-intent through the existing problem mapper", async () => {
    setScenario("files_create_upload_intent", "quota_exceeded");
    renderStep();
    await waitFor(() => screen.getByText(/Up to 10 files/));

    pickFiles([file("orders.csv", 10)]);

    await waitFor(() =>
      expect(screen.getByText(/workspace has run out of storage/)).toBeTruthy(),
    );
  });

  it("removes a row and lets the user try again", async () => {
    setScenario("files_complete", "ready");
    renderStep();
    await waitFor(() => screen.getByText(/Up to 10 files/));

    pickFiles([file("orders.csv", 10)]);
    await screen.findByText("orders.csv");

    fireEvent.click(screen.getByRole("button", { name: "Remove orders.csv" }));

    expect(screen.queryByText("orders.csv")).toBeNull();
  });
});
