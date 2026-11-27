"use client";

import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Circle } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { createDraft, useTemplates } from "@/lib/api/drafts";
import { mapProblem } from "@/lib/api/error-messages";
import { mapFieldErrors } from "@/lib/api/field-errors";
import { createRun, runErrorMessages } from "@/lib/api/runs";
import { useRouter } from "@/i18n/routing";
import { isApiError } from "@/lib/api/problem";
import { FormAlert } from "@/components/features/auth/form-alert";

export interface ReadyFile {
  id: string;
  displayName: string;
}

export interface DescribeStepProps {
  wsId: string;
  files: ReadyFile[];
  onBack: () => void;
}

/** design.md/plan P10.2: a template picker, then assign the uploaded files to its inputs. */
export function DescribeStep({ wsId, files, onBack }: DescribeStepProps) {
  const t = useTranslations();
  const { data: templates } = useTemplates();
  const [templateId, setTemplateId] = useState<string | null>(null);
  const [assignments, setAssignments] = useState<Record<number, string>>({});

  const template = templates?.find((item) => item.id === templateId);

  const mutation = useMutation({
    mutationFn: () => {
      const fileIds = (template?.required_inputs ?? []).map(
        (_, index) => assignments[index],
      );
      return createDraft(
        {
          file_ids: fileIds,
          prompt: "",
          planner: "template",
          template_id: templateId,
          share_samples: false,
        },
        { wsId },
      );
    },
  });

  if (mutation.isSuccess) {
    const { draft } = mutation.data;
    return (
      <div className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold text-ink">
          {t("describe.draftCreatedHeading")}
        </h2>
        <p className="text-sm text-ink-muted">
          {draft.explanation.key
            ? t(
                draft.explanation.key,
                draft.explanation.params as
                  Record<string, string | number> | undefined,
              )
            : draft.explanation.text}
        </p>
        <p className="text-xs text-ink-muted">
          {t("describe.draftId")}{" "}
          <bdi className="select-all font-mono">{draft.id}</bdi>
        </p>
        <ReviewDraft wsId={wsId} draftId={draft.id} />
      </div>
    );
  }

  const apiError = isApiError(mutation.error) ? mutation.error : null;
  const fieldErrors = apiError ? mapFieldErrors(apiError.problem) : null;
  const formAlert: {
    messageKey: string;
    params?: Record<string, unknown>;
    correlationId?: string | null;
  } | null =
    apiError && apiError.problem.code !== "VALIDATION_FAILED"
      ? mapProblem(apiError.problem)
      : (fieldErrors?.form[0] ?? null);
  const templateIdError = fieldErrors?.fields.template_id;
  const fileIdsError = fieldErrors?.fields.file_ids;

  const requiredInputs = template?.required_inputs ?? [];
  const isValid =
    template !== undefined &&
    requiredInputs.length > 0 &&
    requiredInputs.every((_, index) => assignments[index]);

  return (
    <div className="flex flex-col gap-6">
      {formAlert ? (
        <FormAlert
          title={t(
            formAlert.messageKey,
            formAlert.params as Record<string, string | number> | undefined,
          )}
          correlationId={formAlert.correlationId ?? undefined}
          correlationIdLabel={t("errorView.reference")}
        />
      ) : null}

      <div
        role="radiogroup"
        aria-label={t("describe.chooseTemplate")}
        aria-describedby={templateIdError ? "template-id-error" : undefined}
        className="grid gap-3 sm:grid-cols-2"
      >
        {(templates ?? []).map((item) => {
          const checked = item.id === templateId;
          return (
            <div key={item.id} className="relative">
              <input
                type="radio"
                name="template"
                id={`template-${item.id}`}
                checked={checked}
                onChange={() => {
                  setTemplateId(item.id);
                  setAssignments({});
                }}
                className="peer sr-only"
              />
              <label
                htmlFor={`template-${item.id}`}
                className="flex min-h-11 cursor-pointer flex-col gap-1 rounded-panel border-2 border-line p-4 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-focus-ring peer-checked:border-petrol"
              >
                <span className="flex items-center gap-2 font-medium text-ink">
                  {checked ? (
                    <CheckCircle2
                      aria-hidden="true"
                      size={18}
                      strokeWidth={1.75}
                      className="text-petrol"
                    />
                  ) : (
                    <Circle aria-hidden="true" size={18} strokeWidth={1.75} />
                  )}
                  {t(item.title_key)}
                </span>
                <span className="text-sm text-ink-muted">
                  {t(item.description_key)}
                </span>
              </label>
            </div>
          );
        })}
      </div>
      {templateIdError ? (
        <p id="template-id-error" className="text-sm text-missing">
          {t(
            templateIdError.messageKey,
            templateIdError.params as Record<string, string | number>,
          )}
        </p>
      ) : null}

      {template ? (
        <div className="flex flex-col gap-3">
          {requiredInputs.map((input, index) => {
            const usedElsewhere = new Set(
              Object.entries(assignments)
                .filter(([slot]) => Number(slot) !== index)
                .map(([, fileId]) => fileId),
            );
            const fieldError = fieldErrors?.fields[`file_ids.${index}`];
            return (
              <Select
                key={index}
                label={t(input.title_key)}
                placeholder={t("describe.selectFile")}
                value={assignments[index]}
                onValueChange={(value) =>
                  setAssignments((current) => ({ ...current, [index]: value }))
                }
                error={
                  fieldError
                    ? t(
                        fieldError.messageKey,
                        fieldError.params as Record<string, string | number>,
                      )
                    : undefined
                }
                options={files
                  .filter((file) => !usedElsewhere.has(file.id))
                  .map((file) => ({ value: file.id, label: file.displayName }))}
              />
            );
          })}
          {fileIdsError ? (
            <p className="text-sm text-missing">
              {t(
                fileIdsError.messageKey,
                fileIdsError.params as Record<string, string | number>,
              )}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className="flex gap-2">
        <Button variant="secondary" onClick={onBack}>
          {t("describe.back")}
        </Button>
        <Button
          disabled={!isValid || mutation.isPending}
          aria-busy={mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending
            ? t("describe.creatingDraft")
            : t("describe.createDraft")}
        </Button>
      </div>
    </div>
  );
}

function ReviewDraft({ wsId, draftId }: { wsId: string; draftId: string }) {
  const t = useTranslations();
  const router = useRouter();
  const review = useMutation({
    mutationFn: ({ draftId, key }: { draftId: string; key: string }) =>
      createRun(draftId, { wsId, idempotencyKey: key }),
    onSuccess: (run) =>
      router.push(`/runs/${encodeURIComponent(run.id)}/review`),
  });

  return (
    <>
      {review.isError && (
        <ul role="alert">
          {runErrorMessages(review.error).map((message, index) => (
            <li key={index}>
              {t(
                message.messageKey,
                "params" in message
                  ? (message.params as Record<string, string | number>)
                  : undefined,
              )}
            </li>
          ))}
        </ul>
      )}
      <Button
        disabled={review.isPending || review.isSuccess}
        className="self-start"
        onClick={() => review.mutate({ draftId, key: crypto.randomUUID() })}
      >
        {review.isPending ? t("runReview.openingReview") : t("describe.review")}
      </Button>
    </>
  );
}
