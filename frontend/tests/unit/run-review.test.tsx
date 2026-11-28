import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { NextIntlClientProvider } from "next-intl";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ar from "../../messages/ar.json";
import en from "../../messages/en.json";
import { RunReview } from "../../src/components/features/run-review/run-review";
import { PLAN_HASH, RUN_ID, reviewQuestions, run } from "../msw/handlers/runs";
import { setScenario } from "../msw/scenarios";
import { server } from "../msw/server";

const path = `/api/v1/workspaces/ws-1/runs/${RUN_ID}`;
const replace = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));

beforeEach(() => {
  replace.mockClear();
  document.cookie = "replora_csrf=test-token";
});

describe.each([
  { dir: "ltr", locale: "en", messages: en },
  { dir: "rtl", locale: "ar", messages: ar },
] as const)("RunReview ($dir)", ({ dir, locale, messages }) => {
  const labels = messages.runReview;
  const submitLabel = { name: labels.submitAnswers };

  function renderReview() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <div dir={dir}>
        <NextIntlClientProvider messages={messages} locale={locale}>
          <QueryClientProvider client={client}>
            <RunReview wsId="ws-1" runId={RUN_ID} />
          </QueryClientProvider>
        </NextIntlClientProvider>
      </div>,
    );
    return client;
  }

  async function confirm() {
    await waitFor(() => {
      expect(
        screen
          .getByRole("button", { name: labels.approve })
          .hasAttribute("disabled"),
      ).toBe(false);
    });
    fireEvent.click(screen.getByRole("button", { name: labels.approve }));
    const dialog = screen.getByRole("dialog", { name: labels.confirmTitle });
    fireEvent.click(
      within(dialog).getByRole("button", { name: labels.approve }),
    );
  }

  it("approves the loaded plan after confirmation", async () => {
    renderReview();
    await confirm();
    expect(await screen.findByText(RUN_ID)).toBeTruthy();
    expect(
      screen.getByRole("link", { name: labels.openRun }).getAttribute("href"),
    ).toBe(`/${locale}/runs/${RUN_ID}`);
  });

  it("requires a reload before approving a changed plan", async () => {
    setScenario("runs_approve", "PLAN_HASH_MISMATCH");
    renderReview();
    await confirm();
    const reload = await screen.findByRole("button", {
      name: labels.reloadPlan,
    });
    expect(
      screen.getByText(messages.errors.problem.PLAN_HASH_MISMATCH),
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: labels.approve })).toBeNull();
    server.use(
      http.get(path, () =>
        HttpResponse.json({
          ...run,
          plan_hash: PLAN_HASH.replaceAll("a", "b"),
        }),
      ),
    );
    fireEvent.click(reload);
    expect(await screen.findByText("bbbbbbbb")).toBeTruthy();
    expect(
      await screen.findByRole("button", { name: labels.approve }),
    ).toBeTruthy();
  });

  it("refetches after an invalid state conflict and explains expiry", async () => {
    setScenario("runs_approve", "INVALID_STATE_TRANSITION");
    let loads = 0;
    server.use(
      http.get(path, () =>
        HttpResponse.json({
          ...run,
          state: loads++ === 0 ? "AWAITING_APPROVAL" : "EXPIRED",
        }),
      ),
    );
    renderReview();
    await confirm();
    expect(await screen.findByText(labels.expired)).toBeTruthy();
    expect(loads).toBe(2);
    expect(screen.queryByRole("button", { name: labels.approve })).toBeNull();
    expect(screen.queryByText("internal detail")).toBeNull();
  });

  it("shows read-only review issues when the run needs further review", async () => {
    setScenario("runs_get", "NEEDS_REVIEW");
    renderReview();
    expect(
      await screen.findByRole("heading", { name: labels.issues }),
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: labels.approve })).toBeNull();
  });

  function showQuestions() {
    setScenario("runs_get", "REVIEW_QUESTIONS");
    return renderReview();
  }

  async function answerQuestions() {
    const submit = await screen.findByRole<HTMLButtonElement>(
      "button",
      submitLabel,
    );
    const options = screen.getAllByRole("radio", { name: "DMY" });
    expect(submit.disabled).toBe(true);
    fireEvent.click(options[0]);
    expect(submit.disabled).toBe(true);
    fireEvent.click(options[1]);
    expect(submit.disabled).toBe(false);
    return submit;
  }

  it("sends both answers and returns to the run status with the new plan", async () => {
    const requests = vi.fn();
    server.use(
      http.post(`${path}/resolve`, async ({ request }) => {
        requests({
          body: await request.clone().json(),
          key: request.headers.get("Idempotency-Key"),
          csrf: request.headers.get("X-CSRF-Token"),
        });
      }),
    );
    const client = showQuestions();
    const submit = await answerQuestions();
    expect(screen.getByText(reviewQuestions[0].params.column).tagName).toBe(
      "BDI",
    );
    expect(
      screen.getAllByText("DMY").every((option) => option.tagName === "BDI"),
    ).toBe(true);

    setScenario("runs_resolve", "NOT_IMPLEMENTED");
    fireEvent.click(submit);
    expect((await screen.findByRole("alert")).textContent).toBe(
      messages.errors.problem.NOT_IMPLEMENTED,
    );
    fireEvent.click(submit);
    await waitFor(() => expect(requests).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(submit.disabled).toBe(false));
    const [first, second] = requests.mock.calls.map(([request]) => request);
    expect(second.key).toBe(first.key);

    fireEvent.click(screen.getAllByRole("radio", { name: "MDY" })[1]);
    setScenario("runs_resolve", "ok");
    fireEvent.click(submit);

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith(`/${locale}/runs/${RUN_ID}`),
    );
    expect(requests).toHaveBeenLastCalledWith({
      key: expect.stringMatching(/^[a-f0-9-]{36}$/),
      csrf: "test-token",
      body: {
        plan_hash: PLAN_HASH,
        choices: reviewQuestions.map(({ code, path }, index) => ({
          code,
          path,
          value: index === 0 ? "DMY" : "MDY",
        })),
      },
    });
    expect(requests.mock.lastCall?.[0].key).not.toBe(second.key);
    expect(client.getQueryData(["run", "ws-1", RUN_ID])).toMatchObject({
      state: "AWAITING_APPROVAL",
      plan_hash: "b".repeat(64),
    });
  });

  it.each(["PLAN_HASH_MISMATCH", "INVALID_STATE_TRANSITION"] as const)(
    "requires reloading after %s without exposing problem detail",
    async (code) => {
      setScenario("runs_resolve", code);
      showQuestions();
      fireEvent.click(await answerQuestions());
      expect((await screen.findByRole("alert")).textContent).toBe(
        code === "PLAN_HASH_MISMATCH"
          ? labels.answersPlanChanged
          : messages.errors.problem.INVALID_STATE_TRANSITION,
      );
      expect(screen.queryByText("internal detail")).toBeNull();
      expect(screen.queryByRole("button", submitLabel)).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: labels.reloadPlan }));
      const submit = await screen.findByRole<HTMLButtonElement>(
        "button",
        submitLabel,
      );
      expect(submit.disabled).toBe(true);
      expect(replace).not.toHaveBeenCalled();
    },
  );
});
