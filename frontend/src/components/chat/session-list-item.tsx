"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import type { ChatSession } from "@/lib/api/schemas";
import { useRenameSession } from "@/lib/hooks/use-sessions";
import { cn, formatRelativeTime } from "@/lib/utils";

interface SessionListItemProps {
  session: ChatSession;
  active: boolean;
  onDelete: (id: string) => void;
  onNavigate?: () => void;
}

export function SessionListItem({
  session,
  active,
  onDelete,
  onNavigate,
}: SessionListItemProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [editing, setEditing] = useState(false);

  const rename = useRenameSession();

  if (editing) {
    return (
      <RenameField
        initialTitle={session.title}
        onCancel={() => setEditing(false)}
        onSubmit={(title) => {
          setEditing(false);
          if (title && title !== session.title) {
            rename.mutate({ id: session.id, title });
          }
        }}
      />
    );
  }

  return (
    <div
      className={cn(
        "group relative flex items-center rounded-[var(--radius-md)] transition-colors",
        active ? "bg-surface-hover" : "hover:bg-surface-raised",
      )}
      onMouseLeave={() => setMenuOpen(false)}
    >
      <Link
        href={`/chat/${session.id}`}
        onClick={onNavigate}
        className="flex min-w-0 flex-1 flex-col gap-0.5 px-3 py-2.5"
      >
        <span className="truncate text-sm text-foreground">
          {session.title || "New chat"}
        </span>
        <span className="text-xs text-faint">
          {formatRelativeTime(session.created_at)}
        </span>
      </Link>

      <div className="relative pr-1">
        <button
          type="button"
          aria-label="Session actions"
          onClick={() => setMenuOpen((v) => !v)}
          className={cn(
            "grid h-7 w-7 place-items-center rounded-md text-muted transition-opacity hover:bg-surface-hover hover:text-foreground",
            active || menuOpen ? "opacity-100" : "opacity-0 group-hover:opacity-100",
          )}
        >
          <MoreHorizontal className="h-4 w-4" />
        </button>

        {menuOpen && (
          <div
            role="menu"
            className="absolute right-0 top-9 z-20 w-36 overflow-hidden rounded-[var(--radius-md)] border border-border bg-surface-raised py-1 shadow-[var(--shadow-soft)]"
          >
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setMenuOpen(false);
                setEditing(true);
              }}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover"
            >
              <Pencil className="h-4 w-4" />
              Rename
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setMenuOpen(false);
                onDelete(session.id);
              }}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-danger hover:bg-surface-hover"
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/** Inline editable title. Submits on Enter/blur, cancels on Escape. */
function RenameField({
  initialTitle,
  onSubmit,
  onCancel,
}: {
  initialTitle: string;
  onSubmit: (title: string) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(initialTitle);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  return (
    <input
      ref={inputRef}
      value={value}
      maxLength={255}
      onChange={(e) => setValue(e.target.value)}
      onBlur={() => onSubmit(value.trim())}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          onSubmit(value.trim());
        } else if (e.key === "Escape") {
          e.preventDefault();
          onCancel();
        }
      }}
      aria-label="Rename chat"
      className="w-full rounded-[var(--radius-md)] border border-accent/60 bg-surface px-3 py-2.5 text-sm text-foreground outline-none"
    />
  );
}
