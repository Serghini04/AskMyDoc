import { create } from "zustand";

/** Purely client-side UI state. Server state lives in React Query, not here. */
interface UiState {
  /** Sidebar visibility on desktop (persisted within the session). */
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  /** Mobile drawer (separate from desktop collapse). */
  mobileSidebarOpen: boolean;
  setMobileSidebarOpen: (open: boolean) => void;

  /** Documents panel column on desktop (lg and up). */
  documentsPanelOpen: boolean;
  setDocumentsPanelOpen: (open: boolean) => void;

  /** Documents drawer below lg (separate from desktop collapse). */
  mobileDocumentsPanelOpen: boolean;
  setMobileDocumentsPanelOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  mobileSidebarOpen: false,
  setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),

  documentsPanelOpen: true,
  setDocumentsPanelOpen: (open) => set({ documentsPanelOpen: open }),

  mobileDocumentsPanelOpen: false,
  setMobileDocumentsPanelOpen: (open) => set({ mobileDocumentsPanelOpen: open }),
}));
