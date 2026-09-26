import type { Metadata } from "next";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { ClientOnly } from "@/components/util/client-only";

export const metadata: Metadata = {
  title: "AskMyDoc — Chat",
};

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClientOnly
      // Match the shell background so there's no flash before mount.
      fallback={<div className="h-dvh w-full bg-background" />}
    >
      <div className="flex h-dvh w-full overflow-hidden">
        <ChatSidebar />
        <div className="flex min-w-0 flex-1 flex-col">{children}</div>
      </div>
    </ClientOnly>
  );
}
