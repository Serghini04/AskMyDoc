"use client";

import { MessageSquarePlus } from "lucide-react";
import { useCreateSession } from "@/lib/hooks/use-sessions";
import { ChatHeader } from "@/components/chat/chat-header";
import { Button } from "@/components/ui/button";

/** /chat with no session selected — a friendly prompt to start one. */
export default function ChatIndexPage() {
  const createSession = useCreateSession();

  return (
    <>
      <ChatHeader />
      <div className="flex flex-1 items-center justify-center px-4">
        <div className="max-w-md text-center">
          <div className="mx-auto grid h-12 w-12 place-items-center rounded-[var(--radius-lg)] bg-accent-soft text-accent">
            <MessageSquarePlus className="h-6 w-6" strokeWidth={1.75} />
          </div>
          <h1 className="mt-6 font-display text-3xl tracking-tight">
            Start a conversation
          </h1>
          <p className="mt-3 text-sm text-muted">
            Create a new chat, attach a document, and ask away. Your previous
            chats live in the sidebar.
          </p>
          <Button
            className="mt-8"
            size="lg"
            onClick={() => createSession.mutate()}
            disabled={createSession.isPending}
          >
            <MessageSquarePlus className="h-4 w-4" />
            New chat
          </Button>
        </div>
      </div>
    </>
  );
}
