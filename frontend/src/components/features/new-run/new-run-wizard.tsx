"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { DescribeStep } from "@/components/features/describe/describe-step";
import { UploadStep } from "@/components/features/upload/upload-step";
import { useUploadQueue } from "@/components/features/upload/use-upload-queue";

type WizardStep = "upload" | "describe";

export interface NewRunWizardProps {
  wsId: string;
}

/**
 * Owns the upload queue so it survives moving from Upload to Describe: one
 * page, one component tree, no route or context needed for two steps whose
 * state (a handful of already-`ready` server `File` records) already lives
 * in memory here. A later step (Review, Run) that needs this to survive a
 * reload or a real route can promote it to a draft id in the URL instead.
 */
export function NewRunWizard({ wsId }: NewRunWizardProps) {
  const t = useTranslations("newRunWizard");
  const { items, addFiles, removeItem } = useUploadQueue(wsId);
  const [step, setStep] = useState<WizardStep>("upload");

  const readyFiles = items
    .filter((item) => item.status === "ready" && item.serverFile)
    .map((item) => ({
      id: item.serverFile!.id,
      displayName: item.serverFile!.display_name,
    }));

  return (
    <div className="flex flex-col gap-6">
      <ol
        className="flex items-center gap-2 text-sm"
        aria-label={t("stepsLabel")}
      >
        <li
          aria-current={step === "upload" ? "step" : undefined}
          className={
            step === "upload" ? "font-semibold text-ink" : "text-ink-muted"
          }
        >
          1. {t("stepUpload")}
        </li>
        <li aria-hidden="true" className="text-ink-muted">
          ──
        </li>
        <li
          aria-current={step === "describe" ? "step" : undefined}
          className={
            step === "describe" ? "font-semibold text-ink" : "text-ink-muted"
          }
        >
          2. {t("stepDescribe")}
        </li>
      </ol>

      {step === "upload" ? (
        <>
          <UploadStep
            items={items}
            addFiles={addFiles}
            removeItem={removeItem}
          />
          <Button
            className="self-start"
            disabled={readyFiles.length === 0}
            onClick={() => setStep("describe")}
          >
            {t("next")}
          </Button>
        </>
      ) : (
        <DescribeStep
          wsId={wsId}
          files={readyFiles}
          onBack={() => setStep("upload")}
        />
      )}
    </div>
  );
}
