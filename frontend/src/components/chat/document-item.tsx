"use client";

import { Download, FileText, Trash2 } from "lucide-react";
import type { Document } from "@/lib/api/schemas";
import { documentsApi } from "@/lib/api/documents";
import { useDocumentStatus } from "@/lib/hooks/use-documents";
import { formatBytes } from "@/lib/utils";
import { DocumentStatusBadge } from "./document-status";

/**
 * One document in the Documents panel. Polls its own status while processing
 * and exposes download + delete actions.
 */
export function DocumentItem({
  document,
  sessionId,
  onDelete,
}: {
  document: Document;
  sessionId: string;
  onDelete: (id: string) => void;
}) {
  const { data } = useDocumentStatus(document, sessionId);
  const doc = data ?? document;

  return (
    <li className="group flex items-start gap-3 rounded-[var(--radius-md)] px-2.5 py-2.5 hover:bg-surface-hover">
      <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-md bg-surface-raised text-faint">
        <FileText aria-hidden className="h-4 w-4" />
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium" title={doc.filename}>
          {doc.filename}
        </p>
        <p className="mt-0.5 flex items-center gap-1.5 text-xs text-faint">
          {formatBytes(doc.file_size_bytes)}
          <span aria-hidden>·</span>
          <DocumentStatusBadge status={doc.status} />
        </p>
      </div>

      <div className="flex items-center gap-0.5 opacity-60 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
        <a
          href={documentsApi.downloadUrl(doc.id)}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Download ${doc.filename}`}
          className="grid h-7 w-7 place-items-center rounded text-faint hover:bg-surface-raised hover:text-foreground"
        >
          <Download className="h-3.5 w-3.5" />
        </a>
        <button
          type="button"
          aria-label={`Remove ${doc.filename}`}
          onClick={() => onDelete(doc.id)}
          className="grid h-7 w-7 place-items-center rounded text-faint hover:bg-surface-raised hover:text-danger"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </li>
  );
}

/** Placeholder row while the file is still being sent to the server. */
export function UploadingItem({ filename }: { filename: string }) {
  return (
    <li className="flex items-start gap-3 rounded-[var(--radius-md)] border border-dashed border-border px-2.5 py-2.5">
      <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-md bg-surface-raised text-faint">
        <FileText aria-hidden className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium" title={filename}>
          {filename}
        </p>
        <p className="mt-0.5 text-xs">
          <DocumentStatusBadge status="uploading" />
        </p>
      </div>
    </li>
  );
}
