import { FileText, Search } from "lucide-react";

/**
 * A stylized, static mock of the AskMyDoc chat UI — the hero "product shot".
 * Pure markup (no live data) so it renders instantly and never errors.
 */
export function ProductPreview() {
  return (
    <div className="card-surface overflow-hidden rounded-[var(--radius-lg)] border border-border shadow-[var(--shadow-soft)]">
      {/* Window chrome */}
      <div className="flex items-center gap-2 border-b border-border-subtle px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-[var(--ink-600)]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[var(--ink-600)]" />
        <span className="h-2.5 w-2.5 rounded-full bg-[var(--ink-600)]" />
        <div className="ml-3 hidden items-center gap-2 rounded-full border border-border-subtle px-3 py-1 text-xs text-faint sm:flex">
          <Search className="h-3 w-3" />
          AskMyDoc — Annual Report 2025.pdf
        </div>
      </div>

      <div className="grid grid-cols-[180px_1fr] max-sm:grid-cols-1">
        {/* Mini sidebar */}
        <aside className="hidden flex-col gap-1 border-r border-border-subtle p-3 sm:flex">
          <div className="mb-2 rounded-full bg-accent px-3 py-1.5 text-center text-xs font-semibold text-[var(--ink-900)]">
            New chat
          </div>
          {["Annual report Q&A", "Contract review", "Research notes"].map(
            (t, i) => (
              <div
                key={t}
                className={`truncate rounded-md px-2.5 py-2 text-xs ${
                  i === 0 ? "bg-surface-hover text-foreground" : "text-faint"
                }`}
              >
                {t}
              </div>
            ),
          )}
        </aside>

        {/* Conversation */}
        <div className="flex flex-col gap-5 p-5">
          <div className="flex justify-end">
            <div className="max-w-[75%] rounded-2xl rounded-br-md bg-surface-raised px-3.5 py-2 text-xs text-foreground">
              What was total revenue and how did it change YoY?
            </div>
          </div>

          <div className="flex gap-3">
            <div className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-accent font-display text-xs text-[var(--ink-900)]">
              A
            </div>
            <div className="min-w-0 space-y-2 text-xs leading-relaxed text-muted">
              <p>
                Total revenue was{" "}
                <span className="text-foreground">$4.2B in FY2025</span>, up{" "}
                <span className="text-foreground">18% year over year</span> from
                $3.56B.
              </p>
              <div className="flex items-center gap-2 rounded-lg border border-border-subtle bg-surface px-2.5 py-1.5 text-[0.7rem] text-faint">
                <FileText className="h-3 w-3" />
                Source: Annual Report 2025 · p.12, “Financial Highlights”
              </div>
            </div>
          </div>

          {/* Composer */}
          <div className="mt-1 flex items-center gap-2 rounded-full border border-border bg-surface-raised px-2 py-2">
            <div className="h-6 w-6 rounded-full border border-border-subtle" />
            <span className="flex-1 text-xs text-faint">
              Ask anything about your documents…
            </span>
            <span className="h-6 w-6 rounded-full bg-accent" />
          </div>
        </div>
      </div>
    </div>
  );
}
