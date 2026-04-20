import { create } from "zustand";
import { persist } from "zustand/middleware";

import { emptyInventory, type Inventory } from "@/types/api";

interface InventoryState {
  draft: Inventory;
  setDraft: (next: Inventory) => void;
  setCharacter: (character: string) => void;
  patch: (patch: Partial<Inventory>) => void;
  reset: (character?: string) => void;
}

export const useInventoryStore = create<InventoryState>()(
  persist(
    (set) => ({
      draft: emptyInventory("gustave"),
      setDraft: (next) => set({ draft: next }),
      setCharacter: (character) =>
        set((state) => ({
          draft: {
            ...state.draft,
            character,
            // swapping character invalidates character-bound lists
            weapons_available: [],
            skills_known: [],
          },
        })),
      patch: (patch) =>
        set((state) => ({ draft: { ...state.draft, ...patch } })),
      reset: (character = "gustave") => set({ draft: emptyInventory(character) }),
    }),
    { name: "lumina-forge:inventory-draft" },
  ),
);
