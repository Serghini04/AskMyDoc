"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

/** A code block with a copy-to-clipboard affordance in its top-right corner. */
export function CodeBlock({ children }: { children: React.ReactNode }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    const text = extractText(children);
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable — ignore */
    }
  };

  return (
    <div className="group relative">
      <button
        type="button"
        onClick={copy}
        aria-label="Copy code"
        className="absolute right-2 top-2 z-10 grid h-7 w-7 place-items-center rounded-md border border-border bg-surface-raised text-muted opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
      >
        {copied ? (
          <Check className="h-3.5 w-3.5 text-success" />
        ) : (
          <Copy className="h-3.5 w-3.5" />
        )}
      </button>
      <pre>{children}</pre>
    </div>
  );
}

/** Recursively pull plain text out of the rendered code node for copying. */
function extractText(node: React.ReactNode): string {
  if (typeof node === "string") return node;
  if (typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (
    node &&
    typeof node === "object" &&
    "props" in node &&
    (node as { props?: { children?: React.ReactNode } }).props
  ) {
    return extractText(
      (node as { props: { children?: React.ReactNode } }).props.children,
    );
  }
  return "";
}
