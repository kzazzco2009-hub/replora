"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";
import { getApiClient } from "./client";
import { isApiError } from "./problem";
import type { Run, RunIssue } from "./runs";

export type RunState = Run["state"];

const states = {
  DRAFT: true,
  VALIDATED: true,
  AWAITING_APPROVAL: true,
  QUEUED: true,
  RUNNING: true,
  NEEDS_REVIEW: true,
  SUCCEEDED: true,
  PARTIAL: true,
  FAILED: true,
  CANCEL_REQUESTED: true,
  CANCELLED: true,
  EXPIRED: true,
} satisfies Record<RunState, true>;

type EventBase = { seq: number; created_at: string; node_id?: string | null };
// TODO: Use the generated event payload types when the backend schema PR lands.
export type RunEvent = EventBase &
  (
    | { type: "state_changed"; payload: { state: RunState } }
    | {
        type: "node_finished";
        node_id: string;
        payload: { warnings: RunIssue[] };
      }
    | { type: "warning"; payload: { issue: RunIssue } }
  );

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function issue(value: unknown): value is RunIssue {
  return (
    record(value) &&
    typeof value.code === "string" &&
    typeof value.path === "string" &&
    (value.node_id == null || typeof value.node_id === "string") &&
    record(value.params)
  );
}

function isRunEvent(value: unknown): value is RunEvent {
  if (
    !record(value) ||
    typeof value.seq !== "number" ||
    !Number.isSafeInteger(value.seq) ||
    typeof value.created_at !== "string" ||
    (value.node_id != null && typeof value.node_id !== "string") ||
    !record(value.payload)
  )
    return false;

  switch (value.type) {
    case "state_changed":
      return (
        typeof value.payload.state === "string" &&
        Object.hasOwn(states, value.payload.state)
      );
    case "node_finished":
      return (
        typeof value.node_id === "string" &&
        Array.isArray(value.payload.warnings) &&
        value.payload.warnings.every(issue)
      );
    case "warning":
      return issue(value.payload.issue);
    default:
      return false;
  }
}

export async function fetchRunEvents(
  wsId: string,
  runId: string,
  after?: number,
  signal?: AbortSignal,
) {
  const { data } = await getApiClient().GET(
    "/api/v1/workspaces/{ws_id}/runs/{run_id}/events",
    {
      params: { path: { ws_id: wsId, run_id: runId }, query: { after } },
      signal,
    },
  );
  if (!data) throw new Error("Missing run events response");
  const events = Array.isArray(data.events)
    ? data.events.filter(isRunEvent)
    : [];
  return {
    events,
    cursor: Number.isSafeInteger(data.last_seq) ? data.last_seq : after,
  };
}

function subscribeVisibility(notify: () => void) {
  document.addEventListener("visibilitychange", notify);
  return () => document.removeEventListener("visibilitychange", notify);
}

export function runIsLive(state: RunState | undefined) {
  return (
    state === "QUEUED" || state === "RUNNING" || state === "CANCEL_REQUESTED"
  );
}

function pollingDelay(error: unknown, idleDelay: number) {
  if (!error) return idleDelay;
  if (isApiError(error) && error.retryAfter) {
    const seconds = Number(error.retryAfter);
    const delay = Number.isFinite(seconds)
      ? seconds * 1000
      : Date.parse(error.retryAfter) - Date.now();
    if (Number.isFinite(delay)) return Math.max(5_000, delay);
  }
  return 5_000;
}

type Progress = {
  events: RunEvent[];
  cursor?: number;
  state?: RunState;
  delay: number;
};

export const runEventsQueryKey = (wsId: string, runId: string) =>
  ["run-events", wsId, runId] as const;

export function useRunEvents(wsId: string, runId: string, state?: RunState) {
  const client = useQueryClient();
  const visible = useSyncExternalStore(
    subscribeVisibility,
    () => document.visibilityState !== "hidden",
    () => false,
  );
  const queryKey = runEventsQueryKey(wsId, runId);
  const canPoll = (progress?: Progress) =>
    visible && runIsLive(state) && runIsLive(progress?.state ?? state);

  return useQuery({
    queryKey,
    queryFn: async ({ signal }): Promise<Progress> => {
      const previous = client.getQueryData<Progress>(queryKey);
      const page = await fetchRunEvents(wsId, runId, previous?.cursor, signal);
      let cursor = previous?.cursor ?? -Infinity;
      let liveState = previous?.state;
      const events = [...(previous?.events ?? [])];
      for (const event of page.events) {
        if (event.seq <= cursor) continue;
        cursor = event.seq;
        events.push(event);
        if (
          event.type === "state_changed" &&
          !["DRAFT", "VALIDATED", "AWAITING_APPROVAL"].includes(
            event.payload.state,
          )
        )
          liveState = event.payload.state;
      }
      cursor = Math.max(cursor, page.cursor ?? cursor);
      return {
        events,
        cursor: Number.isFinite(cursor) ? cursor : undefined,
        state: liveState,
        delay:
          events.length > (previous?.events.length ?? 0)
            ? 1_000
            : Math.min((previous?.delay ?? 500) * 2, 5_000),
      };
    },
    enabled: (query) => canPoll(query.state.data),
    refetchInterval: (query) =>
      canPoll(query.state.data)
        ? pollingDelay(query.state.error, query.state.data?.delay ?? 1_000)
        : false,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}
