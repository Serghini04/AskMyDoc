"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "./button";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Minimal accessible confirmation modal. Traps initial focus on the confirm
 * button, closes on Escape, and dims the backdrop. Used for destructive
 * actions (delete session / document).
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  destructive = false,
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const confirmRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", onKey);
    confirmRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCancel}
          />
          <motion.div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-title"
            className="relative w-full max-w-sm rounded-[var(--radius-lg)] border border-border bg-surface-raised p-6 shadow-[var(--shadow-soft)]"
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            <h2 id="confirm-title" className="text-lg font-semibold">
              {title}
            </h2>
            {description && (
              <p className="mt-2 text-sm text-muted">{description}</p>
            )}
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" onClick={onCancel} disabled={loading}>
                {cancelLabel}
              </Button>
              <Button
                ref={confirmRef}
                variant={destructive ? "danger" : "primary"}
                onClick={onConfirm}
                disabled={loading}
              >
                {loading ? "Working…" : confirmLabel}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
