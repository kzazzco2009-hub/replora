"use client";

import { useMutation } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { getApiClient } from "@/lib/api/client";
import {
  outputPath,
  resultsErrorKey,
  type OutputLocation,
} from "@/lib/api/results";

function validHref(url: string) {
  const localPath = url.startsWith("/api/");
  if ((!localPath && !/^https?:\/\//i.test(url)) || /[\\\s]/u.test(url))
    return false;
  try {
    const parsed = new URL(url, window.location.origin);
    return localPath
      ? parsed.origin === window.location.origin
      : parsed.protocol === "https:" || parsed.protocol === "http:";
  } catch {
    return false;
  }
}

export function DownloadOutput({
  location,
  filename,
}: {
  location: OutputLocation;
  filename: string;
}) {
  const t = useTranslations();
  const download = useMutation({
    mutationFn: async () => {
      const { data } = await getApiClient().GET(
        "/api/v1/workspaces/{ws_id}/runs/{run_id}/outputs/{artifact_id}/download",
        { params: { path: outputPath(location) }, cache: "no-store" },
      );
      if (
        !data ||
        typeof data.url !== "string" ||
        !validHref(data.url) ||
        typeof data.expires_at !== "string" ||
        !Number.isFinite(Date.parse(data.expires_at))
      )
        throw new Error("Invalid download link");
      if (Date.parse(data.expires_at) <= Date.now()) return "expired";
      const anchor = document.createElement("a");
      anchor.setAttribute("href", data.url);
      anchor.rel = "noopener";
      anchor.click();
      return "started";
    },
  });
  const error = download.isError
    ? t(resultsErrorKey(download.error))
    : download.data === "expired"
      ? t("results.downloadExpired")
      : null;
  return (
    <div>
      <Button
        variant="secondary"
        aria-label={t("results.downloadFile", { filename })}
        disabled={download.isPending}
        onClick={() => download.mutate()}
        className="min-w-11"
      >
        <Download aria-hidden="true" size={18} />
        {t(
          download.isPending ? "results.preparingDownload" : "results.download",
        )}
      </Button>
      {error && (
        <p role="alert" className="mt-2 text-sm">
          {error}
        </p>
      )}
    </div>
  );
}
