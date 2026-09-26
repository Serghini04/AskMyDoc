"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowDown, RotateCw } from "lucide-react";
import type { ChatMessage, Document } from "@/lib/api/schemas";
import { MessageBubble } from "./message-bubble";
import { DocumentEvent } from "./document-event";
import { TypingIndicator } from "./typing-indicator";

type TimelineItem =
  | { kind: "message"; at: number; message: ChatMessage }
  | { kind: "document"; at: number; document: Document };

/** Messages and "document added" receipts, in the order they happened. */
function buildTimeline(messages: ChatMessage[], documents: Document[]) {
  const items: TimelineItem[] = [
    ...messages.map((message) => ({
      kind: "message" as const,
      at: Date.parse(message.created_at),
      message,
    })),
    ...documents.map((document) => ({
      kind: "document" as const,
      at: Date.parse(document.created_at),
      document,
    })),
  ];
  // Stable sort keeps same-timestamp items in their original order.
  return items.sort((a, b) => a.at - b.at);
}

interface MessageListProps {
  messages: ChatMessage[];
  documents: Document[];
  awaitingReply: boolean;
  error: string | null;
  onRetry: () => void;
}

export function MessageList({
  messages,
  documents,
  awaitingReply,
  error,
  onRetry,
}: MessageListProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [atBottom, setAtBottom] = useState(true);
  const timeline = buildTimeline(messages, documents);

  // Auto-scroll to newest only when the user is already near the bottom.
  useEffect(() => {
    if (atBottom) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [timeline.length, awaitingReply, atBottom]);

  const onScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setAtBottom(distance < 120);
  };

  return (
    <div className="relative flex-1 overflow-hidden">
      <div
        ref={containerRef}
        onScroll={onScroll}
        className="scroll-thin h-full overflow-y-auto"
      >
        <div className="mx-auto flex max-w-3xl flex-col gap-8 px-4 py-8">
          {timeline.map((item) =>
            item.kind === "message" ? (
              <MessageBubble key={item.message.id} message={item.message} />
            ) : (
              <DocumentEvent key={`doc-${item.document.id}`} document={item.document} />
            ),
          )}

          {awaitingReply && (
            <div className="flex gap-3.5">
              <div
                aria-hidden
                className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-md bg-accent font-display text-sm text-[var(--ink-900)]"
              >
                A
              </div>
              <div className="pt-2">
                <TypingIndicator />
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-between gap-3 rounded-[var(--radius-md)] border border-danger/40 bg-[rgba(224,122,106,0.08)] px-4 py-3 text-sm">
              <span className="text-danger">{error}</span>
              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-foreground hover:bg-surface-hover"
              >
                <RotateCw className="h-3.5 w-3.5" />
                Retry
              </button>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {!atBottom && (
        <button
          type="button"
          aria-label="Scroll to latest"
          onClick={() =>
            bottomRef.current?.scrollIntoView({ behavior: "smooth" })
          }
          className="absolute bottom-4 left-1/2 grid h-9 w-9 -translate-x-1/2 place-items-center rounded-full border border-border bg-surface-raised text-muted shadow-[var(--shadow-soft)] hover:text-foreground"
        >
          <ArrowDown className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
