import { notFound } from "next/navigation";
import { TokensPreview } from "./tokens-preview-client";

/** Dev-only token reference. Never served in production. */
export default function TokensPreviewPage() {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }

  return <TokensPreview />;
}
