import { env } from "@/lib/env";
import { apiClient } from "./client";
import { documentSchema, type Document } from "./schemas";

/** Allowed upload types + size, mirroring the backend constraints. */
export const ALLOWED_EXTENSIONS = [".pdf", ".txt"] as const;
export const MAX_UPLOAD_MB = 50;

/** Endpoints under /documents — see backend app/api/routers/documents.py. */
export const documentsApi = {
  upload: (sessionId: string, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("file", file);
    return apiClient.postForm("/documents/", documentSchema, formData);
  },

  get: (id: string, signal?: AbortSignal): Promise<Document> =>
    apiClient.get(`/documents/${id}`, documentSchema, signal),

  remove: (id: string): Promise<void> => apiClient.delete(`/documents/${id}`),

  /** Direct browser download URL (served by the backend FileResponse). */
  downloadUrl: (id: string): string =>
    `${env.apiBaseUrl}/documents/${id}/download`,
};

/** Client-side validation before we bother the server. */
export function validateFile(file: File): string | null {
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext as (typeof ALLOWED_EXTENSIONS)[number])) {
    return `Unsupported file type. Only ${ALLOWED_EXTENSIONS.join(" and ")} are allowed.`;
  }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return `File is too large. Maximum size is ${MAX_UPLOAD_MB} MB.`;
  }
  return null;
}
