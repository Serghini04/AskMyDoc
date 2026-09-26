"use client";

import { useState } from "react";
import {
  QueryClient,
  QueryClientProvider,
  defaultShouldDehydrateQuery,
} from "@tanstack/react-query";
import { ApiError } from "@/lib/api/client";

/**
 * App-wide React Query provider. One client per browser session, created lazily
 * so it isn't shared across requests during SSR.
 */
export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: (failureCount, error) => {
              // Don't retry user-correctable errors (404/409/413/...).
              if (error instanceof ApiError && error.isClientError) return false;
              return failureCount < 2;
            },
          },
          dehydrate: {
            shouldDehydrateQuery: (query) =>
              defaultShouldDehydrateQuery(query),
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
