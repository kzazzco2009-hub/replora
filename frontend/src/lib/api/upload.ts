import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { getApiClient } from "./client";
import type { components } from "./schema";

export type Limits = components["schemas"]["Limits"];
type ContractFile = components["schemas"]["File"];
export type UploadedFile = Omit<ContractFile, "detected_type"> & {
  detected_type: ContractFile["detected_type"] | "json";
};

export const limitsQueryKey = ["limits"] as const;

/** `GET /limits` (public, cacheable): the server limits the UI enforces up front. */
export function useLimits(): UseQueryResult<Limits> {
  return useQuery({
    queryKey: limitsQueryKey,
    queryFn: async () => {
      const { data } = await getApiClient().GET("/api/v1/limits");
      if (data === undefined) {
        throw new Error("GET /limits resolved with no data and no error");
      }
      return data;
    },
  });
}

export type UploadLimitIssue = "file_too_large" | "too_many_files";

/** `errors.problem.FILE_TOO_LARGE` is reused: the same file, the same message, whether the server or this check catches it first. */
export const UPLOAD_LIMIT_MESSAGE_KEYS: Record<UploadLimitIssue, string> = {
  file_too_large: "errors.problem.FILE_TOO_LARGE",
  too_many_files: "upload.tooManyFiles",
};

/**
 * Client-side size and count checks only (design.md, P10.1); the server
 * still re-checks and decides on `upload-intent`. `selectedCount` is the
 * total number of files the user is about to upload, including this one.
 */
export function validateBeforeUpload(
  file: File,
  limits: Limits,
  selectedCount: number,
): UploadLimitIssue | null {
  if (file.size > limits.max_file_size) return "file_too_large";
  if (selectedCount > limits.max_files_per_run) return "too_many_files";
  return null;
}

export interface UploadFileOptions {
  /** Required by the contract's path parameter; not in the caller-facing shape by choice, but still mandatory here. */
  wsId: string;
  onProgress?: (fraction: number) => void;
  signal?: AbortSignal;
}

/**
 * PUTs `file`'s raw bytes to `url`, using exactly the given headers (never
 * built or guessed on the client) and no other headers — same-origin CSRF
 * doesn't apply here (client.ts), and a signed storage URL would reject an
 * unexpected header. Uses XMLHttpRequest, not fetch, for upload progress.
 */
function putToStorage(
  url: string,
  headers: Record<string, string>,
  file: File,
  onProgress?: (fraction: number) => void,
  signal?: AbortSignal,
): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Upload aborted", "AbortError"));
      return;
    }
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    for (const [name, value] of Object.entries(headers)) {
      xhr.setRequestHeader(name, value);
    }
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(event.loaded / event.total);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error(`Upload PUT failed with status ${xhr.status}`));
    };
    xhr.onerror = () => reject(new Error("Upload PUT failed"));
    xhr.onabort = () =>
      reject(new DOMException("Upload aborted", "AbortError"));
    signal?.addEventListener("abort", () => xhr.abort());
    xhr.send(file);
  });
}

/**
 * `upload-intent` -> PUT the exact returned URL/method/headers -> `complete`.
 * Resolves to the completed `File` (`ready` with `detected_type`, or
 * `rejected` with `rejection_code`); never throws for a rejection, only for
 * a transport or contract-level failure (network, auth, 413, 422, …).
 */
export async function uploadFile(
  file: File,
  { wsId, onProgress, signal }: UploadFileOptions,
): Promise<UploadedFile> {
  const client = getApiClient();

  const { data: intent } = await client.POST(
    "/api/v1/workspaces/{ws_id}/files/upload-intent",
    {
      params: { path: { ws_id: wsId } },
      body: {
        display_name: file.name,
        size: file.size,
        content_type: file.type || "application/octet-stream",
      },
      signal,
    },
  );
  if (intent === undefined) {
    throw new Error("upload-intent resolved with no data and no error");
  }

  await putToStorage(
    intent.upload.url,
    intent.upload.headers,
    file,
    onProgress,
    signal,
  );

  const { data: completed } = await client.POST(
    "/api/v1/workspaces/{ws_id}/files/{file_id}/complete",
    {
      params: { path: { ws_id: wsId, file_id: intent.file_id } },
      signal,
    },
  );
  if (completed === undefined) {
    throw new Error("complete resolved with no data and no error");
  }
  return completed;
}
