"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Plus, PanelLeftClose, X } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  useSessions,
  useCreateSession,
  useDeleteSession,
} from "@/lib/hooks/use-sessions";
import { useUiStore } from "@/lib/store/ui-store";
import { cn } from "@/lib/utils";
import { SessionListItem } from "./session-list-item";

export function ChatSidebar() {
  const pathname = usePathname();
  const activeId = pathname.split("/chat/")[1] ?? null;

  const { data: sessions, isLoading, isError } = useSessions();
  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();

  const { sidebarOpen, toggleSidebar, mobileSidebarOpen, setMobileSidebarOpen } =
    useUiStore();

  const [pendingDelete, setPendingDelete] = useState<string | null>(null);

  const content = (
    <div className="flex h-full w-72 flex-col bg-surface">
      <div className="flex items-center justify-between px-4 py-4">
        <Logo />
        <button
          type="button"
          aria-label="Collapse sidebar"
          onClick={toggleSidebar}
          className="hidden h-8 w-8 place-items-center rounded-md text-muted hover:bg-surface-hover hover:text-foreground md:grid"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
        <button
          type="button"
          aria-label="Close menu"
          onClick={() => setMobileSidebarOpen(false)}
          className="grid h-8 w-8 place-items-center rounded-md text-muted hover:bg-surface-hover md:hidden"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="px-3">
        <Button
          variant="secondary"
          className="w-full justify-start"
          onClick={() => createSession.mutate()}
          disabled={createSession.isPending}
        >
          <Plus className="h-4 w-4" />
          New chat
        </Button>
      </div>

      <nav className="scroll-thin mt-4 flex-1 space-y-1 overflow-y-auto px-3 pb-4">
        {isLoading && (
          <div className="space-y-2 px-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="h-12 animate-pulse rounded-[var(--radius-md)] bg-surface-raised"
              />
            ))}
          </div>
        )}

        {isError && (
          <p className="px-3 py-4 text-sm text-danger">
            Couldn&apos;t load chats. Is the API running?
          </p>
        )}

        {sessions?.length === 0 && (
          <p className="px-3 py-4 text-sm text-faint">
            No chats yet. Start a new one.
          </p>
        )}

        {sessions?.map((session) => (
          <SessionListItem
            key={session.id}
            session={session}
            active={session.id === activeId}
            onDelete={setPendingDelete}
            onNavigate={() => setMobileSidebarOpen(false)}
          />
        ))}
      </nav>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete chat?"
        description="This permanently removes the conversation, its messages, and any documents attached to it."
        confirmLabel="Delete"
        destructive
        loading={deleteSession.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete) {
            deleteSession.mutate(pendingDelete, {
              onSettled: () => setPendingDelete(null),
            });
          }
        }}
      />
    </div>
  );

  return (
    <>
      {/* Desktop: collapsible inline column */}
      <aside
        className={cn(
          "hidden shrink-0 border-r border-border-subtle transition-[width] duration-200 md:block",
          sidebarOpen ? "w-72" : "w-0 overflow-hidden",
        )}
      >
        {content}
      </aside>

      {/* Mobile: slide-over drawer */}
      <AnimatePresence>
        {mobileSidebarOpen && (
          <div className="fixed inset-0 z-50 md:hidden">
            <motion.div
              className="absolute inset-0 bg-black/60"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileSidebarOpen(false)}
            />
            <motion.div
              className="absolute left-0 top-0 h-full border-r border-border-subtle"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            >
              {content}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
