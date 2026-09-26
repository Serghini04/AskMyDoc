"use client";

import { use } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { useSession } from "@/lib/hooks/use-sessions";
import { ApiError } from "@/lib/api/client";
import { ConversationView } from "@/components/chat/conversation-view";
import { ChatHeader } from "@/components/chat/chat-header";
import { buttonVariants } from "@/components/ui/button";

export default function SessionPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = use(params);
  const { data: session, isLoading, error } = useSession(sessionId);

  if (isLoading) {
    return (
      <>
        <ChatHeader />
        <div className="flex flex-1 items-center justify-center text-muted">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      </>
    );
  }

  if (error || !session) {
    const notFound = error instanceof ApiError && error.status === 404;
    return (
      <>
        <ChatHeader />
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 text-center">
          <p className="text-muted">
            {notFound
              ? "This chat doesn't exist or was deleted."
              : "Couldn't load this chat. Check that the API is reachable."}
          </p>
          <Link href="/chat" className={buttonVariants({ variant: "secondary" })}>
            Back to chats
          </Link>
        </div>
      </>
    );
  }

  return <ConversationView session={session} />;
}
