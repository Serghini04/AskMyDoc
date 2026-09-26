"use client";

import { useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { documentsApi, validateFile } from "@/lib/api/documents";
import { ApiError } from "@/lib/api/client";
import {
  isDocumentInProgress,
  type ChatSession,
  type Document,
} from "@/lib/api/schemas";
import { queryKeys } from "./query-keys";

/** Upload a document to a session, then refresh the session's document list. */
export function useUploadDocument(sessionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => documentsApi.upload(sessionId, file),
    onSuccess: (doc) => {
      queryClient.setQueryData<ChatSession>(
        queryKeys.session(sessionId),
        (prev) =>
          prev ? { ...prev, documents: [...prev.documents, doc] } : prev,
      );
    },
  });
}

/** Delete a document and drop it from the session cache. */
export function useDeleteDocument(sessionId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => documentsApi.remove(id),
    onSuccess: (_data, id) => {
      queryClient.setQueryData<ChatSession>(
        queryKeys.session(sessionId),
        (prev) =>
          prev
            ? { ...prev, documents: prev.documents.filter((d) => d.id !== id) }
            : prev,
      );
    },
  });
}

/**
 * Poll a single document's status until it settles. Processing is async on the
 * backend, so we refetch every 2s while a doc is still pending/processing.
 */
export function useDocumentStatus(doc: Document, sessionId: string) {
  const queryClient = useQueryClient();
  const isPending = isDocumentInProgress(doc.status);

  return useQuery({
    queryKey: queryKeys.document(doc.id),
    queryFn: async ({ signal }) => {
      const fresh = await documentsApi.get(doc.id, signal);
      // Keep the parent session's embedded copy in sync as status changes.
      queryClient.setQueryData<ChatSession>(
        queryKeys.session(sessionId),
        (prev) =>
          prev
            ? {
                ...prev,
                documents: prev.documents.map((d) =>
                  d.id === fresh.id ? fresh : d,
                ),
              }
            : prev,
      );
      return fresh;
    },
    initialData: doc,
    enabled: isPending,
    refetchInterval: (query) =>
      query.state.data && isDocumentInProgress(query.state.data.status)
        ? 2000
        : false,
  });
}

/**
 * Validated upload with user-facing error text. Shared by the composer's
 * paperclip and the documents panel so both show the same in-flight state.
 */
export function useDocumentUploader(sessionId: string) {
  const upload = useUploadDocument(sessionId);
  const [error, setError] = useState<string | null>(null);

  const uploadFile = (file: File) => {
    const invalid = validateFile(file);
    if (invalid) {
      setError(invalid);
      return;
    }
    setError(null);
    upload.mutate(file, {
      onError: (err) => {
        setError(
          err instanceof ApiError
            ? err.status === 409
              ? "That file is already in this chat."
              : err.message
            : "Upload failed. Please try again.",
        );
      },
    });
  };

  return {
    uploadFile,
    error,
    clearError: () => setError(null),
    isUploading: upload.isPending,
    uploadingName: upload.isPending ? upload.variables?.name : undefined,
  };
}

export type DocumentUploader = ReturnType<typeof useDocumentUploader>;
