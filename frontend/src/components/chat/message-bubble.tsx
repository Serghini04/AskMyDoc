"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import type { ChatMessage } from "@/lib/api/schemas";
import { cn } from "@/lib/utils";
import { Markdown } from "./markdown";

/**
 * A single message. User messages are right-aligned bubbles; assistant messages
 * are full-width Markdown with a copy action on hover.
 */
export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] whitespace-pre-wrap rounded-[var(--radius-lg)] rounded-br-md bg-surface-raised px-4 py-2.5 text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    );
  }

  return <AssistantMessage message={message} />;
}

function AssistantMessage({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="group flex gap-3.5">
      <div
        aria-hidden
        className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-md bg-accent font-display text-sm text-[var(--ink-900)]"
      >
        A
      </div>
      <div className="min-w-0 flex-1">
        <Markdown content={message.content} />
        <button
          type="button"
          onClick={copy}
          aria-label="Copy answer"
          className={cn(
            "mt-2 inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-faint transition-opacity hover:bg-surface-raised hover:text-foreground",
            "opacity-0 group-hover:opacity-100 focus-visible:opacity-100",
          )}
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-success" /> Copied
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" /> Copy
            </>
          )}
        </button>
      </div>
    </div>
  );
}
