import { apiClient } from "./client";
import {
  chatMessageSchema,
  chatSessionListSchema,
  chatSessionSchema,
  type ChatMessage,
  type ChatSession,
} from "./schemas";

/** Endpoints under /sessions — see backend app/api/routers/chat.py. */
export const sessionsApi = {
  list: (signal?: AbortSignal): Promise<ChatSession[]> =>
    apiClient.get("/sessions/", chatSessionListSchema, signal),

  get: (id: string, signal?: AbortSignal): Promise<ChatSession> =>
    apiClient.get(`/sessions/${id}`, chatSessionSchema, signal),

  create: (): Promise<ChatSession> =>
    apiClient.post("/sessions/", chatSessionSchema),

  rename: (id: string, title: string): Promise<ChatSession> =>
    apiClient.patch(`/sessions/${id}`, chatSessionSchema, { title }),

  remove: (id: string): Promise<void> => apiClient.delete(`/sessions/${id}`),

  /**
   * The RAG endpoint. Request/response (not streaming) — returns the assistant
   * message once generation completes. Isolated here so a future streaming
   * upgrade touches one function.
   */
  sendMessage: (sessionId: string, message: string): Promise<ChatMessage> =>
    apiClient.post(`/sessions/${sessionId}/chat`, chatMessageSchema, {
      message,
    }),
};
