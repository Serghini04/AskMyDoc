"use client";

import { FileUp, Sparkles } from "lucide-react";
import { isDocumentInProgress, type Document } from "@/lib/api/schemas";
import { DocumentEvent } from "./document-event";

const suggestions = [
  "Summarize this document in five bullet points.",
  "What are the key dates and figures mentioned?",
  "Explain the main argument in plain language.",
];

/** Shown inside a session that has no messages yet. */
export function EmptyConversation({
  documents,
  onPick,
}: {
  documents: Document[];
  onPick: (text: string) => void;
}) {
  const hasDocuments = documents.length > 0;
  // Asking before anything is indexed would get a "no information" answer.
  const hasReadyDocument = documents.some(
    (d) => d.status === "completed",
  );
  const allIndexing = hasDocuments && documents.every((d) => isDocumentInProgress(d.status));

  return (
    <div className="flex flex-1 items-center justify-center px-4">
      <div className="w-full max-w-lg text-center">
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-[var(--radius-lg)] bg-accent-soft text-accent">
          <Sparkles className="h-6 w-6" strokeWidth={1.75} />
        </div>
        <h1 className="mt-6 font-display text-3xl tracking-tight">
          What can I help you find?
        </h1>

        {hasDocuments ? (
          <>
            <div className="mt-6 flex flex-col gap-2">
              {documents.map((doc) => (
                <DocumentEvent key={doc.id} document={doc} />
              ))}
            </div>
            <p className="mt-6 text-sm text-muted">
              {allIndexing
                ? "Reading your document — suggestions unlock once it's ready."
                : "Ask a question, or try one of these to get started."}
            </p>
            <div className="mt-6 flex flex-col gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => onPick(s)}
                  disabled={!hasReadyDocument}
                  className="rounded-[var(--radius-md)] border border-border bg-surface-raised px-4 py-3 text-left text-sm text-foreground transition-colors hover:border-accent/50 hover:bg-surface-hover disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-border disabled:hover:bg-surface-raised"
                >
                  {s}
                </button>
              ))}
            </div>
          </>
        ) : (
          <div className="mt-6 flex items-center justify-center gap-2 rounded-[var(--radius-md)] border border-dashed border-border px-4 py-5 text-sm text-muted">
            <FileUp className="h-4 w-4 text-accent" />
            Attach a PDF or text file below to begin.
          </div>
        )}
      </div>
    </div>
  );
}
