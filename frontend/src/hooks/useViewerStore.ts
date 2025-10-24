import { create } from 'zustand';

type ViewerSource = { source: 'generated'; filename: string } | { source: 'dataset'; id: number; filename: string };

interface ViewerState {
  selectedFile: ViewerSource | null;
  setSelectedFile: (file: ViewerSource | null) => void;
  lastUpdated: number;
  touch: () => void;
}

export const useViewerStore = create<ViewerState>((set) => ({
  selectedFile: null,
  lastUpdated: Date.now(),
  setSelectedFile: (file) => set({ selectedFile: file }),
  touch: () => set({ lastUpdated: Date.now() })
}));
