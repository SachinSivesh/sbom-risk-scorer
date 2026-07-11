import { create } from 'zustand';

interface UiState {
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  currentApplicationName: string | null;
  setCurrentApplicationName: (name: string | null) => void;
  currentSbomId: string | null;
  setCurrentSbomId: (id: string | null) => void;
  isUploadOpen: boolean;
  setIsUploadOpen: (open: boolean) => void;
  selectedApplicationId: string | null;
  setSelectedApplicationId: (id: string | null) => void;
}

export const useUiStore = create<UiState>((set) => ({
  selectedNodeId: null,
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  activeTab: 'summary',
  setActiveTab: (tab) => set({ activeTab: tab }),
  currentApplicationName: null,
  setCurrentApplicationName: (name) => set({ currentApplicationName: name }),
  currentSbomId: null,
  setCurrentSbomId: (id) => set({ currentSbomId: id }),
  isUploadOpen: false,
  setIsUploadOpen: (open) => set({ isUploadOpen: open }),
  selectedApplicationId: null,
  setSelectedApplicationId: (id) => set({ selectedApplicationId: id }),
}));
