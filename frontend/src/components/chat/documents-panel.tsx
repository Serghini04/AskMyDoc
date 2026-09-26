"use client";

import { useRef, useState } from "react";
import { FileUp, Plus, X } from "lucide-react";
import type { Document } from "@/lib/api/schemas";
import { ALLOWED_EXTENSIONS, MAX_UPLOAD_MB } from "@/lib/api/documents";
import { useDeleteDocument, type DocumentUploader } from "@/lib/hooks/use-documents";
import { useUiStore } from "@/lib/store/ui-store";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { cn } from "@/lib/utils";
import { DocumentItem, UploadingItem } from "./document-item";

/**
 * The chat's library: every file answers can draw from, with its status.
 * Deliberately separate from the composer so received documents never look
 * like a draft attachment waiting to be sent.
 *
 * Always mounted (hidden with CSS when closed) so each item keeps polling its
 * status even while the panel isn't visible.
 */
export function DocumentsPanel({
  sessionId,
  documents,
  uploader,
}: {
  sessionId: string;
  documents: Document[];
  uploader: DocumentUploader;
}) {
  const {
    documentsPanelOpen,
    setDocumentsPanelOpen,
    mobileDocumentsPanelOpen,
    setMobileDocumentsPanelOpen,
  } = useUiStore();

  const close = () => {
    setDocumentsPanelOpen(false);
    setMobileDocumentsPanelOpen(false);
  };
  const deleteDoc = useDeleteDocument(sessionId);
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isEmpty = documents.length === 0 && !uploader.uploadingName;

  const onFilePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-selecting the same file
    if (file) uploader.uploadFile(file);
  };

  return (
    <>
      {/* Backdrop for the drawer on small screens */}
      {mobileDocumentsPanelOpen && (
        <div
          aria-hidden
          onClick={() => setMobileDocumentsPanelOpen(false)}
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
        />
      )}

      <aside
        id="documents-panel"
        aria-label="Documents in this chat"
        className={cn(
          "flex w-80 shrink-0 flex-col border-l border-border-subtle bg-surface",
          "fixed inset-y-0 right-0 z-40 transition-transform duration-200 lg:static lg:z-auto lg:translate-x-0",
          mobileDocumentsPanelOpen ? "translate-x-0" : "translate-x-full",
          !documentsPanelOpen && "lg:hidden",
        )}
      >
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-border-subtle px-4">
          <h2 className="text-sm font-medium">
            Documents
            {documents.length > 0 && (
              <span className="ml-1.5 text-faint">{documents.length}</span>
            )}
          </h2>
          <button
            type="button"
            aria-label="Close documents"
            onClick={close}
            className="grid h-8 w-8 place-items-center rounded-md text-muted hover:bg-surface-hover hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="scroll-thin flex-1 overflow-y-auto p-3">
          <p className="px-2.5 pb-3 text-xs leading-relaxed text-faint">
            Every answer in this chat is grounded in these files.
          </p>

          {isEmpty ? (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex w-full flex-col items-center gap-2 rounded-[var(--radius-md)] border border-dashed border-border px-4 py-8 text-center text-sm text-muted hover:border-accent/50 hover:text-foreground"
            >
              <FileUp className="h-5 w-5 text-accent" />
              Add a PDF or text file
              <span className="text-xs text-faint">Up to {MAX_UPLOAD_MB} MB</span>
            </button>
          ) : (
            <ul className="flex flex-col gap-1">
              {documents.map((doc) => (
                <DocumentItem
                  key={doc.id}
                  document={doc}
                  sessionId={sessionId}
                  onDelete={setPendingDelete}
                />
              ))}
              {uploader.uploadingName && (
                <UploadingItem filename={uploader.uploadingName} />
              )}
            </ul>
          )}

          {uploader.error && (
            <p role="alert" className="mt-3 px-2.5 text-xs text-danger">
              {uploader.error}
            </p>
          )}
        </div>

        {!isEmpty && (
          <div className="border-t border-border-subtle p-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploader.isUploading}
              className="flex w-full items-center justify-center gap-2 rounded-[var(--radius-md)] border border-border px-3 py-2 text-sm text-muted hover:bg-surface-hover hover:text-foreground disabled:opacity-50"
            >
              <Plus className="h-4 w-4" />
              Add document
            </button>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={ALLOWED_EXTENSIONS.join(",")}
          className="hidden"
          onChange={onFilePick}
        />
      </aside>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Remove document?"
        description="This deletes the file and its indexed content from this chat."
        confirmLabel="Remove"
        destructive
        loading={deleteDoc.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete) {
            deleteDoc.mutate(pendingDelete, {
              onSettled: () => setPendingDelete(null),
            });
          }
        }}
      />
    </>
  );
}
