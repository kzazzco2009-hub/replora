import { AlertTriangle } from "lucide-react";
export interface FormAlertProps {
  title: string;
  correlationId?: string;
  correlationIdLabel?: string;
}

/** Inline form-level error: icon + text, never colour alone (design.md §3). */
export function FormAlert({
  title,
  correlationId,
  correlationIdLabel,
}: FormAlertProps) {
  return (
    <div
      role="alert"
      className="flex items-start gap-2 rounded-panel border border-line bg-surface-raised p-3 text-sm text-ink"
    >
      <AlertTriangle
        aria-hidden="true"
        size={20}
        strokeWidth={1.75}
        className="mt-0.5 shrink-0 text-missing"
      />
      <div className="flex-1">
        <p>{title}</p>
        {correlationId ? (
          <p className="mt-1 text-xs text-ink-muted">
            {correlationIdLabel}{" "}
            <span className="select-all font-mono">{correlationId}</span>
          </p>
        ) : null}
      </div>
    </div>
  );
}
