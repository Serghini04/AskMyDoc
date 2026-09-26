import { z } from "zod";

/**
 * Zod schemas mirror the FastAPI response models exactly (see backend
 * app/schemas). We validate at the network boundary so the rest of the app can
 * trust its types instead of hoping the server matches.
 */

export const documentStatusSchema = z.enum([
  "pending",
  "processing",
  "completed",
  "failed",
]);
export type DocumentStatus = z.infer<typeof documentStatusSchema>;

/** Still being ingested — not yet searchable. */
export const isDocumentInProgress = (status: string) =>
  status === "pending" || status === "processing";

export const documentSchema = z.object({
  id: z.string().uuid(),
  filename: z.string(),
  file_hash: z.string(),
  file_size_bytes: z.number(),
  // The backend sends uppercase (PENDING, PROCESSING...); normalize here so the
  // UI compares against DocumentStatus values. Unknown values pass through.
  status: z.string().transform((s) => s.toLowerCase()),
  session_id: z.string().uuid(),
  created_at: z.string(),
});
export type Document = z.infer<typeof documentSchema>;

export const chatRoleSchema = z.enum(["user", "assistant"]);
export type ChatRole = z.infer<typeof chatRoleSchema>;

export const chatMessageSchema = z.object({
  id: z.string().uuid(),
  session_id: z.string().uuid(),
  role: chatRoleSchema,
  content: z.string(),
  created_at: z.string(),
});
export type ChatMessage = z.infer<typeof chatMessageSchema>;

export const chatSessionSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  created_at: z.string(),
  messages: z.array(chatMessageSchema).default([]),
  documents: z.array(documentSchema).default([]),
});
export type ChatSession = z.infer<typeof chatSessionSchema>;

export const chatSessionListSchema = z.array(chatSessionSchema);
export const documentListSchema = z.array(documentSchema);
