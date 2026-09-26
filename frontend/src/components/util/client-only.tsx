"use client";

import { useSyncExternalStore } from "react";

const noopSubscribe = () => () => {};

/**
 * Renders children only after the component has mounted on the client.
 *
 * The chat surface is an authless, data-driven app shell (it needs the browser,
 * React Query, and the API to render anything meaningful), so server-rendering
 * it adds no value. Gating it on mount also means there is no server HTML for
 * DOM-mutating browser extensions (e.g. Dark Reader) to alter *before*
 * hydration — which is the usual source of spurious hydration mismatches on
 * icon `<svg>` elements. Icons then appear in a normal post-mount render where
 * such mutations are harmless.
 */
export function ClientOnly({
  children,
  fallback = null,
}: {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  // false during SSR and hydration, true on the client afterwards — without
  // a setState-in-effect re-render.
  const mounted = useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  );

  return <>{mounted ? children : fallback}</>;
}
