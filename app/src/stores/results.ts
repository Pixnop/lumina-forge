import { create } from "zustand";

import type { OptimizeResponse, RankedBuildResponse } from "@/types/api";

interface ResultsState {
  last: OptimizeResponse | null;
  setResults: (response: OptimizeResponse) => void;
  findByRank: (rank: number) => RankedBuildResponse | undefined;
}

export const useResultsStore = create<ResultsState>()((set, get) => ({
  last: null,
  setResults: (response) => set({ last: response }),
  findByRank: (rank) =>
    get().last?.builds.find((b) => b.rank === rank),
}));
