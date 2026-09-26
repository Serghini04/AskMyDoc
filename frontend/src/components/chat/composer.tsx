"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Paperclip } from "lucide-react";
import { isDocumentInProgress, type Document } from "@/lib/api/schemas";
import { ALLOWED_EXTENSIONS } from "@/lib/api/documents";
import type { DocumentUploader } from "@/lib/hooks/use-documents";
import { cn } from "@/lib/utils";

interface ComposerProps {
  documents: Document[];
  uploader: DocumentUploader;
  /** Disable input while a reply is generating. */
  sending: boolean;
  onSend: (message: string) => void;
}

const MAX_LENGTH = 4000;

/**
 * Message input only. Received documents live in the DocumentsPanel; the
 * paperclip here is just a shortcut into the same upload flow.
 */
export function Composer({ documents, uploader, sending, onSend }: ComposerProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-grow the textarea up to a max height.
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const indexing = documents.filter((d) => isDocumentInProgress(d.status));
  // Nothing searchable yet — a question now could only get a "no info" answer.
  const waitingForIndex = documents.length > 0 && indexing.length === documents.length;

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || sending || waitingForIndex) return;
    onSend(trimmed);
    setValue("");
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const onFilePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-selecting the same file
    if (file) uploader.uploadFile(file);
  };

  return (
    <div className="border-t border-border-subtle bg-background">
      <div className="mx-auto w-full max-w-3xl px-4 py-4">
        {/* The panel shows upload errors on desktop; it's a drawer below lg. */}
        {uploader.error && (
          <p role="alert" className="mb-2 text-xs text-danger lg:hidden">
            {uploader.error}
          </p>
        )}

        <div className="flex items-end gap-2 rounded-[var(--radius-lg)] border border-border bg-surface-raised p-2 transition-colors focus-within:border-accent/60">
          <button
            type="button"
            aria-label="Add a document to this chat"
            title="Add a document to this chat"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploader.isUploading}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-[var(--radius-md)] text-muted hover:bg-surface-hover hover:text-foreground disabled:opacity-50"
          >
            <Paperclip
              className={cn("h-[18px] w-[18px]", uploader.isUploading && "animate-pulse")}
            />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.join(",")}
            className="hidden"
            onChange={onFilePick}
          />

          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value.slice(0, MAX_LENGTH))}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder={
              waitingForIndex
                ? "Hang on — your document is being indexed…"
                : "Ask anything about your documents…"
            }
            aria-label="Message"
            className="scroll-thin max-h-[200px] flex-1 resize-none bg-transparent py-2 text-sm leading-relaxed text-foreground outline-none placeholder:text-faint"
          />

          <button
            type="button"
            aria-label="Send message"
            onClick={submit}
            disabled={!value.trim() || sending || waitingForIndex}
            className="grid h-9 w-9 shrink-0 place-items-center rounded-[var(--radius-md)] bg-accent text-[var(--ink-900)] transition-opacity hover:bg-accent-strong disabled:opacity-30"
          >
            <ArrowUp className="h-[18px] w-[18px]" strokeWidth={2.25} />
          </button>
        </div>

        {indexing.length > 0 ? (
          <p role="status" className="mt-2 px-1 text-center text-[0.7rem] text-muted">
            {indexing.length === 1
              ? `${indexing[0].filename} is still being indexed`
              : `${indexing.length} documents are still being indexed`}
            {" "}— answers won&apos;t include {indexing.length === 1 ? "it" : "them"} yet.
          </p>
        ) : (
          <p className="mt-2 px-1 text-center text-[0.7rem] text-faint">
            Answers are grounded in the documents in this chat. Press Enter to
            send, Shift+Enter for a new line.
          </p>
        )}
      </div>
    </div>
  );
}
