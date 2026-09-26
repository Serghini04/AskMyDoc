"use client";

import { useRef } from "react";
import type { ChatSession } from "@/lib/api/schemas";
import { useSendMessage } from "@/lib/hooks/use-chat";
import { useDocumentUploader } from "@/lib/hooks/use-documents";
import { ApiError } from "@/lib/api/client";
import { ChatHeader } from "./chat-header";
import { MessageList } from "./message-list";
import { Composer } from "./composer";
import { EmptyConversation } from "./empty-conversation";
import { DocumentsPanel } from "./documents-panel";

/**
 * Orchestrates a single conversation: history + composer on the left, the
 * chat's documents in their own panel on the right.
 */
export function ConversationView({ session }: { session: ChatSession }) {
  const send = useSendMessage(session.id);
  const uploader = useDocumentUploader(session.id);
  const lastAttempt = useRef<string>("");

  const handleSend = (message: string) => {
    lastAttempt.current = message;
    send.mutate(message);
  };

  const errorMessage = send.isError
    ? send.error instanceof ApiError
      ? send.error.message
      : "Something went wrong generating a reply."
    : null;

  const hasMessages = session.messages.length > 0;
  const showConversation = hasMessages || send.isPending || send.isError;

  return (
    <>
      <ChatHeader
        title={session.title}
        documentCount={session.documents.length}
      />

      <div className="flex min-h-0 flex-1">
        <div className="flex min-w-0 flex-1 flex-col">
          {showConversation ? (
            <MessageList
              messages={session.messages}
              documents={session.documents}
              awaitingReply={send.isPending}
              error={errorMessage}
              onRetry={() =>
                lastAttempt.current && handleSend(lastAttempt.current)
              }
            />
          ) : (
            <EmptyConversation
              documents={session.documents}
              onPick={handleSend}
            />
          )}

          <Composer
            documents={session.documents}
            uploader={uploader}
            sending={send.isPending}
            onSend={handleSend}
          />
        </div>

        <DocumentsPanel
          sessionId={session.id}
          documents={session.documents}
          uploader={uploader}
        />
      </div>
    </>
  );
}
