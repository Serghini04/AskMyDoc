"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { sessionsApi } from "@/lib/api/sessions";
import type { ChatSession } from "@/lib/api/schemas";
import { queryKeys } from "./query-keys";

/** Sidebar history: all sessions, newest first. */
export function useSessions() {
  return useQuery({
    queryKey: queryKeys.sessions,
    queryFn: ({ signal }) => sessionsApi.list(signal),
    select: (sessions) =>
      [...sessions].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      ),
  });
}

/** A single session with its messages and documents. */
export function useSession(id: string | undefined) {
  return useQuery({
    queryKey: id ? queryKeys.session(id) : ["sessions", "none"],
    queryFn: ({ signal }) => sessionsApi.get(id as string, signal),
    enabled: Boolean(id),
  });
}

/** Create a new session and navigate to it ("New Chat"). */
export function useCreateSession() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: () => sessionsApi.create(),
    onSuccess: (session) => {
      queryClient.setQueryData(queryKeys.session(session.id), session);
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions });
      router.push(`/chat/${session.id}`);
    },
  });
}

/** Rename a session, optimistically updating the sidebar and detail caches. */
export function useRenameSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) =>
      sessionsApi.rename(id, title),

    onMutate: async ({ id, title }) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.sessions });
      const previousList = queryClient.getQueryData<ChatSession[]>(
        queryKeys.sessions,
      );

      queryClient.setQueryData<ChatSession[]>(queryKeys.sessions, (prev) =>
        prev?.map((s) => (s.id === id ? { ...s, title } : s)),
      );
      queryClient.setQueryData<ChatSession>(queryKeys.session(id), (prev) =>
        prev ? { ...prev, title } : prev,
      );

      return { previousList };
    },

    onError: (_error, _vars, context) => {
      if (context?.previousList) {
        queryClient.setQueryData(queryKeys.sessions, context.previousList);
      }
    },

    onSuccess: (session) => {
      queryClient.setQueryData(queryKeys.session(session.id), session);
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions });
    },
  });
}

/** Delete a session; redirect away if the user was viewing it. */
export function useDeleteSession() {
  const queryClient = useQueryClient();
  const router = useRouter();

  return useMutation({
    mutationFn: (id: string) => sessionsApi.remove(id),
    onSuccess: (_data, id) => {
      queryClient.setQueryData<ChatSession[]>(queryKeys.sessions, (prev) =>
        prev?.filter((s) => s.id !== id),
      );
      queryClient.removeQueries({ queryKey: queryKeys.session(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions });
    },
    onSettled: (_d, _e, id) => {
      if (typeof window !== "undefined" && window.location.pathname.includes(id)) {
        router.push("/chat");
      }
    },
  });
}
