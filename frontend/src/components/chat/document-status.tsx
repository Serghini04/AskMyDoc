import { CheckCircle2, Loader2, TriangleAlert } from "lucide-react";
import { isDocumentInProgress } from "@/lib/api/schemas";
import { cn } from "@/lib/utils";

/** Client-only state for a file still in flight to the server. */
export type DocumentDisplayStatus = string | "uploading";

const LABELS = {
  uploading: "Uploading…",
  indexing: "Indexing…",
  ready: "Ready",
  failed: "Failed",
} as const;

function resolve(status: DocumentDisplayStatus): keyof typeof LABELS {
  if (status === "uploading") return "uploading";
  if (isDocumentInProgress(status)) return "indexing";
  if (status === "failed") return "failed";
  return "ready";
}

const HINTS: Record<keyof typeof LABELS, string> = {
  uploading: "Sending the file to the server",
  indexing: "Reading and indexing — answers won't use this file until it's ready",
  ready: "Indexed — answers in this chat can use this file",
  failed: "Processing failed — remove and re-upload this file",
};

/** Icon + word for a document's lifecycle, so status never relies on color alone. */
export function DocumentStatusBadge({
  status,
  className,
}: {
  status: DocumentDisplayStatus;
  className?: string;
}) {
  const state = resolve(status);
  const Icon =
    state === "ready" ? CheckCircle2 : state === "failed" ? TriangleAlert : Loader2;

  return (
    <span
      title={HINTS[state]}
      className={cn(
        "inline-flex items-center gap-1 whitespace-nowrap",
        state === "ready" && "text-success",
        state === "failed" && "text-danger",
        (state === "uploading" || state === "indexing") && "text-muted",
        className,
      )}
    >
      <Icon
        aria-hidden
        className={cn(
          "h-3.5 w-3.5",
          (state === "uploading" || state === "indexing") && "animate-spin",
        )}
      />
      {LABELS[state]}
    </span>
  );
}
