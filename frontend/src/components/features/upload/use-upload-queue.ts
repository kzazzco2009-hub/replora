"use client";

import { useCallback, useState } from "react";
import { isApiError, type Problem } from "@/lib/api/problem";
import type { RejectionCode } from "@/lib/api/rejection-messages";
import {
  uploadFile,
  validateBeforeUpload,
  type Limits,
  type UploadLimitIssue,
} from "@/lib/api/upload";

export type UploadItemStatus =
  "uploading" | "ready" | "rejected" | "blocked" | "error";

export interface UploadItem {
  id: string;
  file: File;
  status: UploadItemStatus;
  progress: number;
  detectedType?: "csv" | "zip" | null;
  rejectionCode?: RejectionCode;
  blockedIssue?: UploadLimitIssue;
  problem?: Problem;
}

/** Drives one workspace's upload queue: client pre-check, then intent -> PUT -> complete per file. */
export function useUploadQueue(wsId: string) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [controllers] = useState(() => new Map<string, AbortController>());

  const patchItem = useCallback((id: string, patch: Partial<UploadItem>) => {
    setItems((current) =>
      current.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    );
  }, []);

  const addFiles = useCallback(
    (files: File[], limits: Limits | undefined) => {
      const selectedCount = items.length + files.length;
      const newItems: UploadItem[] = files.map((file) => ({
        id: crypto.randomUUID(),
        file,
        status: "uploading",
        progress: 0,
      }));
      setItems((current) => [...current, ...newItems]);

      for (const item of newItems) {
        const issue = limits
          ? validateBeforeUpload(item.file, limits, selectedCount)
          : null;
        if (issue) {
          patchItem(item.id, { status: "blocked", blockedIssue: issue });
          continue;
        }

        const controller = new AbortController();
        controllers.set(item.id, controller);
        uploadFile(item.file, {
          wsId,
          signal: controller.signal,
          onProgress: (fraction) => patchItem(item.id, { progress: fraction }),
        })
          .then((result) => {
            if (result.status === "rejected") {
              patchItem(item.id, {
                status: "rejected",
                rejectionCode: result.rejection_code ?? undefined,
              });
            } else {
              patchItem(item.id, {
                status: "ready",
                detectedType: result.detected_type,
              });
            }
          })
          .catch((error: unknown) => {
            if (error instanceof DOMException && error.name === "AbortError") {
              return;
            }
            patchItem(item.id, {
              status: "error",
              problem: isApiError(error) ? error.problem : undefined,
            });
          })
          .finally(() => controllers.delete(item.id));
      }
    },
    [controllers, items.length, patchItem, wsId],
  );

  const removeItem = useCallback(
    (id: string) => {
      controllers.get(id)?.abort();
      controllers.delete(id);
      setItems((current) => current.filter((item) => item.id !== id));
    },
    [controllers],
  );

  return { items, addFiles, removeItem };
}
