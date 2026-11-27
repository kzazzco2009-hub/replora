"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  X,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { mapProblem } from "@/lib/api/error-messages";
import { mapRejectionCode } from "@/lib/api/rejection-messages";
import { UPLOAD_LIMIT_MESSAGE_KEYS } from "@/lib/api/upload";
import { formatBytes } from "./format-bytes";
import type { UploadItem } from "./use-upload-queue";

type StatusTone = "muted" | "ok" | "missing" | "diff";

const STATUS_ICON: Record<UploadItem["status"], LucideIcon> = {
  uploading: Loader2,
  ready: CheckCircle2,
  rejected: XCircle,
  blocked: AlertTriangle,
  error: XCircle,
};

const STATUS_TONE: Record<UploadItem["status"], StatusTone> = {
  uploading: "muted",
  ready: "ok",
  rejected: "missing",
  blocked: "diff",
  error: "missing",
};

const TONE_CLASSES: Record<StatusTone, string> = {
  muted: "text-ink-muted",
  ok: "text-ok",
  missing: "text-missing",
  diff: "text-diff",
};

export interface FileRowProps {
  item: UploadItem;
  onRemove: (id: string) => void;
}

export function FileRow({ item, onRemove }: FileRowProps) {
  const t = useTranslations();
  const Icon = STATUS_ICON[item.status];
  const tone = TONE_CLASSES[STATUS_TONE[item.status]];

  let statusText: string;
  switch (item.status) {
    case "uploading":
      statusText = t("upload.uploading", {
        percent: Math.round(item.progress * 100),
      });
      break;
    case "ready":
      statusText = t("upload.ready", {
        type: (item.detectedType ?? "").toUpperCase(),
      });
      break;
    case "rejected":
      statusText = item.rejectionCode
        ? t(mapRejectionCode(item.rejectionCode))
        : t("upload.rejected");
      break;
    case "blocked":
      statusText = item.blockedIssue
        ? t(UPLOAD_LIMIT_MESSAGE_KEYS[item.blockedIssue])
        : t("upload.failed");
      break;
    case "error":
      statusText = item.problem
        ? t(mapProblem(item.problem).messageKey)
        : t("upload.failed");
      break;
  }

  return (
    <li className="flex items-center gap-3 rounded-panel border border-line bg-surface p-3">
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-ink">
          <bdi>{item.file.name}</bdi>
        </p>
        <p className="text-xs text-ink-muted">
          <span dir="ltr">{formatBytes(item.file.size)}</span>
        </p>
        {item.status === "uploading" ? (
          <div
            role="progressbar"
            aria-valuenow={Math.round(item.progress * 100)}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={item.file.name}
            className="mt-2 h-2 overflow-hidden rounded-chip bg-line"
          >
            <div
              className="h-full bg-petrol transition-[width] duration-300 motion-reduce:transition-none"
              style={{ width: `${Math.round(item.progress * 100)}%` }}
            />
          </div>
        ) : null}
        <p className={`mt-1 flex items-center gap-1 text-xs ${tone}`}>
          <Icon
            aria-hidden="true"
            size={14}
            strokeWidth={1.75}
            className={
              item.status === "uploading"
                ? "animate-spin motion-reduce:animate-none"
                : undefined
            }
          />
          {statusText}
        </p>
      </div>
      <button
        type="button"
        onClick={() => onRemove(item.id)}
        aria-label={t("upload.remove", { name: item.file.name })}
        className="flex min-h-11 min-w-11 items-center justify-center rounded-control text-ink-muted outline-offset-2 hover:bg-surface-raised focus-visible:outline-2 focus-visible:outline-focus-ring"
      >
        <X aria-hidden="true" size={18} strokeWidth={1.75} />
      </button>
    </li>
  );
}
