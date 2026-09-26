/** Centralized query keys so invalidation stays consistent and typo-free. */
export const queryKeys = {
  sessions: ["sessions"] as const,
  session: (id: string) => ["sessions", id] as const,
  document: (id: string) => ["documents", id] as const,
};
