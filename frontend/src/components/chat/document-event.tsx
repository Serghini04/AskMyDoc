import { FileText } from "lucide-react";
import type { Document } from "@/lib/api/schemas";
import { formatBytes } from "@/lib/utils";
import { DocumentStatusBadge } from "./document-status";

/**
 * A receipt in the conversation timeline: "file.pdf added to this chat".
 * Confirms the upload where the user is looking and keeps a record of when
 * each document joined the chat.
 */
export function DocumentEvent({ document }: { document: Document }) {
  return (
    <div className="flex justify-center">
      <div className="flex max-w-full items-center gap-2 rounded-full border border-border-subtle bg-surface px-3.5 py-1.5 text-xs text-muted">
        <FileText aria-hidden className="h-3.5 w-3.5 shrink-0 text-faint" />
        <span className="min-w-0 truncate">
          <span className="font-medium text-foreground" title={document.filename}>
            {document.filename}
          </span>{" "}
          added to this chat
        </span>
        <span className="text-faint">· {formatBytes(document.file_size_bytes)} ·</span>
        <DocumentStatusBadge status={document.status} />
      </div>
    </div>
  );
}
