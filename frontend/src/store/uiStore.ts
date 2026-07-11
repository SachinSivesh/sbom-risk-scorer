import { create } from 'zustand';

interface UiState {
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const useUiStore = create<UiState>((set) => ({
  selectedNodeId: null,
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  activeTab: 'summary',
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
