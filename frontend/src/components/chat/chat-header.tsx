"use client";

import {
  FileText,
  Menu,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Plus,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/lib/store/ui-store";
import { useCreateSession } from "@/lib/hooks/use-sessions";

/** Top bar for the conversation area: menu/expand controls + current title. */
export function ChatHeader({
  title,
  documentCount,
}: {
  title?: string;
  /** When set, shows a button toggling the Documents panel. */
  documentCount?: number;
}) {
  const {
    sidebarOpen,
    setSidebarOpen,
    setMobileSidebarOpen,
    documentsPanelOpen,
    setDocumentsPanelOpen,
    mobileDocumentsPanelOpen,
    setMobileDocumentsPanelOpen,
  } = useUiStore();

  // Desktop toggles the column; smaller screens toggle the drawer.
  const toggleDocuments = () => {
    if (window.matchMedia("(min-width: 1024px)").matches) {
      setDocumentsPanelOpen(!documentsPanelOpen);
    } else {
      setMobileDocumentsPanelOpen(!mobileDocumentsPanelOpen);
    }
  };
  const createSession = useCreateSession();

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border-subtle px-3">
      {/* Mobile: open drawer */}
      <button
        type="button"
        aria-label="Open menu"
        onClick={() => setMobileSidebarOpen(true)}
        className="grid h-9 w-9 place-items-center rounded-md text-muted hover:bg-surface-hover hover:text-foreground md:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Desktop: expand collapsed sidebar */}
      {!sidebarOpen && (
        <button
          type="button"
          aria-label="Expand sidebar"
          onClick={() => setSidebarOpen(true)}
          className="hidden h-9 w-9 place-items-center rounded-md text-muted hover:bg-surface-hover hover:text-foreground md:grid"
        >
          <PanelLeftOpen className="h-5 w-5" />
        </button>
      )}

      <h1 className="min-w-0 flex-1 truncate text-sm font-medium text-muted">
        {title ?? "AskMyDoc"}
      </h1>

      {documentCount !== undefined && (
        <button
          type="button"
          onClick={toggleDocuments}
          aria-controls="documents-panel"
          aria-expanded={documentsPanelOpen}
          title={documentsPanelOpen ? "Hide documents" : "Show documents"}
          className={cn(
            "inline-flex h-9 items-center gap-1.5 rounded-md px-2.5 text-sm text-muted hover:bg-surface-hover hover:text-foreground",
            documentsPanelOpen && "lg:bg-surface-raised lg:text-foreground",
          )}
        >
          {documentsPanelOpen ? (
            <PanelRightClose className="hidden h-4 w-4 lg:block" />
          ) : (
            <PanelRightOpen className="hidden h-4 w-4 lg:block" />
          )}
          <FileText className="h-4 w-4 lg:hidden" />
          Documents
          {documentCount > 0 && <span className="text-faint">{documentCount}</span>}
        </button>
      )}

      <button
        type="button"
        aria-label="New chat"
        onClick={() => createSession.mutate()}
        disabled={createSession.isPending}
        className="grid h-9 w-9 place-items-center rounded-md text-muted hover:bg-surface-hover hover:text-foreground disabled:opacity-50 md:hidden"
      >
        <Plus className="h-5 w-5" />
      </button>
    </header>
  );
}
