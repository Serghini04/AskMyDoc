"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sessionsApi } from "@/lib/api/sessions";
import type { ChatMessage, ChatSession } from "@/lib/api/schemas";
import { queryKeys } from "./query-keys";

/** Stable client-only ids for optimistic messages (no crypto dependency). */
let tempCounter = 0;
const tempId = () => `temp-${Date.now()}-${tempCounter++}`;

/**
 * Send a message in a session. Optimistically appends the user's message so the
 * UI feels instant, then appends the assistant reply when it returns. On error
 * the optimistic message is rolled back so the user can retry without losing it.
 */
export function useSendMessage(sessionId: string) {
  const queryClient = useQueryClient();
  const key = queryKeys.session(sessionId);

  return useMutation({
    mutationFn: (message: string) =>
      sessionsApi.sendMessage(sessionId, message),

    onMutate: async (message) => {
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<ChatSession>(key);

      const optimisticUser: ChatMessage = {
        id: tempId(),
        session_id: sessionId,
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      };

      queryClient.setQueryData<ChatSession>(key, (prev) =>
        prev
          ? { ...prev, messages: [...prev.messages, optimisticUser] }
          : prev,
      );

      return { previous, optimisticUserId: optimisticUser.id };
    },

    onSuccess: (assistantMessage) => {
      // The server persisted the real user message too; refetch to reconcile
      // ids/titles. Append the assistant reply immediately for snappiness.
      queryClient.setQueryData<ChatSession>(key, (prev) =>
        prev
          ? { ...prev, messages: [...prev.messages, assistantMessage] }
          : prev,
      );
      queryClient.invalidateQueries({ queryKey: key });
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions });
    },

    onError: (_error, _message, context) => {
      // Roll back the optimistic user message; the composer keeps the text.
      if (context?.previous) {
        queryClient.setQueryData(key, context.previous);
      }
    },
  });
}
