"use client";

import { UploadCloud } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { useLimits } from "@/lib/api/upload";
import { formatBytes } from "./format-bytes";
import { FileRow } from "./file-row";
import { useUploadQueue } from "./use-upload-queue";

export interface UploadStepProps {
  wsId: string;
}

/** design.md "New run, Upload": drop zone (the empty state) plus a file picker and per-file rows. */
export function UploadStep({ wsId }: UploadStepProps) {
  const t = useTranslations();
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: limits } = useLimits();
  const { items, addFiles, removeItem } = useUploadQueue(wsId);
  const [dragOver, setDragOver] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const previousStatuses = useRef(new Map<string, string>());

  useEffect(() => {
    for (const item of items) {
      const previous = previousStatuses.current.get(item.id);
      if (previous !== item.status && item.status !== "uploading") {
        previousStatuses.current.set(item.id, item.status);
        const label =
          item.status === "ready"
            ? t("upload.ready", {
                type: (item.detectedType ?? "").toUpperCase(),
              })
            : item.status === "rejected"
              ? t("upload.rejected")
              : t("upload.failed");
        setAnnouncement(`${item.file.name}: ${label}`);
      }
    }
  }, [items, t]);

  function handleFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    addFiles(Array.from(fileList), limits);
  }

  return (
    <div className="flex flex-col gap-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragOver(false);
          handleFiles(event.dataTransfer.files);
        }}
        className={`flex flex-col items-center gap-3 rounded-panel border-2 border-dashed p-8 text-center ${
          dragOver ? "border-petrol bg-surface-raised" : "border-line"
        }`}
      >
        <UploadCloud
          aria-hidden="true"
          size={32}
          strokeWidth={1.5}
          className="text-ink-muted"
        />
        <p className="text-sm text-ink-muted">{t("upload.dropHint")}</p>
        <Button variant="secondary" onClick={() => inputRef.current?.click()}>
          {t("upload.browse")}
        </Button>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="sr-only"
          onChange={(event) => {
            handleFiles(event.target.files);
            event.target.value = "";
          }}
        />
        {limits ? (
          <p className="text-xs text-ink-muted">
            {t("upload.limitsHint", {
              maxFiles: limits.max_files_per_run,
              maxSize: formatBytes(limits.max_file_size),
            })}
          </p>
        ) : null}
      </div>

      <div role="status" aria-live="polite" className="sr-only">
        {announcement}
      </div>

      {items.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {items.map((item) => (
            <FileRow key={item.id} item={item} onRemove={removeItem} />
          ))}
        </ul>
      ) : null}
    </div>
  );
}
