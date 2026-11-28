"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { isApiError } from "@/lib/api/problem";
import { runEventsQueryKey } from "@/lib/api/run-events";
import {
  resolveRun,
  reviewOptions,
  runErrorMessages,
  runQueryKey,
  type Run,
} from "@/lib/api/runs";
import { IssueMessage } from "./run-plan";

export function RunResolve({
  wsId,
  run,
  reload,
}: {
  wsId: string;
  run: Run;
  reload: () => Promise<boolean>;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const client = useQueryClient();
  const id = useId();
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [reloading, setReloading] = useState(false);
  const attempt = useRef<{ body: string; key: string } | null>(null);
  const questions = run.review_issues.flatMap((issue) => {
    const options = reviewOptions(issue);
    return options ? [{ issue, options }] : [];
  });
  const choices = questions.flatMap(({ issue, options }, index) => {
    const value = options[answers[index]];
    return value === undefined
      ? []
      : [{ code: issue.code, path: issue.path, value }];
  });
  const resolve = useMutation({
    mutationFn: (input: Parameters<typeof resolveRun>[2]) =>
      resolveRun(wsId, run.id, input),
    onSuccess: async (updated) => {
      const key = runQueryKey(wsId, run.id);
      await client.cancelQueries({ queryKey: key });
      client.removeQueries({ queryKey: runEventsQueryKey(wsId, run.id) });
      client.setQueryData(key, updated);
      router.replace(`/${locale}/runs/${encodeURIComponent(run.id)}`);
    },
  });

  if (!questions.length) return null;
  const problem = isApiError(resolve.error) ? resolve.error.problem : undefined;
  const conflict = problem?.status === 409 ? problem.code : undefined;
  const reloadRequired =
    conflict === "PLAN_HASH_MISMATCH" ||
    conflict === "INVALID_STATE_TRANSITION";
  const errorKey =
    conflict === "PLAN_HASH_MISMATCH"
      ? "runReview.answersPlanChanged"
      : problem?.status === 501
        ? "errors.problem.NOT_IMPLEMENTED"
        : runErrorMessages(resolve.error)[0].messageKey;
  const busy = resolve.isPending || reloading;
  const complete = choices.length === questions.length && choices.length <= 100;

  async function reloadPlan() {
    setReloading(true);
    if (await reload()) {
      setAnswers({});
      attempt.current = null;
      resolve.reset();
    }
    setReloading(false);
  }

  return (
    <form
      aria-labelledby={id}
      className="flex flex-col items-start gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        if (!complete || busy || reloadRequired) return;
        const body = JSON.stringify([run.plan_hash, choices]);
        if (attempt.current?.body !== body) {
          attempt.current = { body, key: crypto.randomUUID() };
        }
        resolve.mutate({
          planHash: run.plan_hash,
          choices,
          idempotencyKey: attempt.current.key,
        });
      }}
    >
      <h2 id={id} className="font-semibold">
        {t("runReview.answerQuestions")}
      </h2>
      {questions.map(({ issue, options }, index) => {
        const column = issue.params?.column;
        return (
          <fieldset
            key={index}
            disabled={busy || reloadRequired}
            className="[min-inline-size:0]"
          >
            <legend className="font-medium">
              <IssueMessage issue={issue} />
              {typeof column === "string" && (
                <bdi className="block whitespace-pre-wrap wrap-anywhere">
                  {column}
                </bdi>
              )}
            </legend>
            {options.map((value, optionIndex) => (
              <label
                key={optionIndex}
                className="flex items-center gap-2 [min-block-size:44px]"
              >
                <input
                  type="radio"
                  name={`${id}-${index}`}
                  required
                  checked={answers[index] === optionIndex}
                  onChange={() =>
                    setAnswers((current) => ({
                      ...current,
                      [index]: optionIndex,
                    }))
                  }
                />
                <bdi className="whitespace-pre-wrap wrap-anywhere">
                  {typeof value === "string" && value
                    ? value
                    : JSON.stringify(value)}
                </bdi>
              </label>
            ))}
          </fieldset>
        );
      })}
      {resolve.isError && <p role="alert">{t(errorKey)}</p>}
      {reloadRequired ? (
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => void reloadPlan()}
        >
          {t("runReview.reloadPlan")}
        </Button>
      ) : (
        <Button
          type="submit"
          disabled={!complete || busy}
          aria-busy={resolve.isPending}
          className="motion-reduce:transition-none"
        >
          {t("runReview.submitAnswers")}
        </Button>
      )}
    </form>
  );
}
