import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  Clock,
  Copy,
  Eye,
  FileEdit,
  Loader2,
  Stamp,
  XCircle,
  type LucideIcon,
} from "lucide-react";

export type StatusChipStatus =
  | "matched"
  | "value_diff"
  | "missing_left"
  | "missing_right"
  | "duplicate_key"
  | "DRAFT"
  | "VALIDATED"
  | "AWAITING_APPROVAL"
  | "QUEUED"
  | "RUNNING"
  | "NEEDS_REVIEW"
  | "SUCCEEDED"
  | "PARTIAL"
  | "FAILED"
  | "CANCEL_REQUESTED"
  | "CANCELLED"
  | "EXPIRED";

type StatusColor = "ok" | "diff" | "missing" | "review" | "saffron" | "muted";

const COLOR_CLASSES: Record<StatusColor, string> = {
  ok: "text-ok",
  diff: "text-diff",
  missing: "text-missing",
  review: "text-review",
  saffron: "text-saffron",
  muted: "text-ink-muted",
};

/** design.md §3: matched/succeeded, value_diff/partial, missing/failed and
 * needs-review map to the four defined status colours. AWAITING_APPROVAL
 * gets saffron (reserved for "approval and attention"); the remaining
 * lifecycle states have no defined colour, so they stay muted. */
const STATUS_STYLES: Record<
  StatusChipStatus,
  { icon: LucideIcon; color: StatusColor }
> = {
  matched: { icon: CheckCircle2, color: "ok" },
  SUCCEEDED: { icon: CheckCircle2, color: "ok" },
  value_diff: { icon: AlertTriangle, color: "diff" },
  duplicate_key: { icon: Copy, color: "diff" },
  PARTIAL: { icon: AlertTriangle, color: "diff" },
  missing_left: { icon: XCircle, color: "missing" },
  missing_right: { icon: XCircle, color: "missing" },
  FAILED: { icon: XCircle, color: "missing" },
  NEEDS_REVIEW: { icon: Eye, color: "review" },
  DRAFT: { icon: FileEdit, color: "muted" },
  VALIDATED: { icon: CheckCircle2, color: "muted" },
  AWAITING_APPROVAL: { icon: Stamp, color: "saffron" },
  QUEUED: { icon: Clock, color: "muted" },
  RUNNING: { icon: Loader2, color: "muted" },
  CANCEL_REQUESTED: { icon: Ban, color: "muted" },
  CANCELLED: { icon: Ban, color: "muted" },
  EXPIRED: { icon: Clock, color: "muted" },
};

export interface StatusChipProps {
  status: StatusChipStatus;
  /** Always a translated string from the caller; never hard-coded here. */
  label: string;
}

/** design.md §3: status is never shown by colour alone — icon + text, always. */
export function StatusChip({ status, label }: StatusChipProps) {
  const { icon: Icon, color } = STATUS_STYLES[status];

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-chip border border-line bg-surface px-2.5 py-0.5 text-xs font-medium [min-block-size:44px] ${COLOR_CLASSES[color]}`}
    >
      <Icon aria-hidden="true" size={14} strokeWidth={1.75} />
      {label}
    </span>
  );
}
