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
            // Swapping character invalidates *all* the character-bound lists.
            // Pictos and luminas aren't character-bound in the game, but the
            // ones the player actually owns are tied to their playthrough
            // state; resetting them keeps the form honest after a manual
            // character swap (use the save importer to repopulate).
            weapons_available: [],
            skills_known: [],
            pictos_available: [],
            pictos_mastered: [],
            luminas_extra: [],
            attributes: { might: 0, agility: 0, defense: 0, luck: 0, vitality: 0 },
            level: 1,
            pp_budget: 0,
          },
        })),
      patch: (patch) =>
        set((state) => ({ draft: { ...state.draft, ...patch } })),
      reset: (character = "gustave") => set({ draft: emptyInventory(character) }),
    }),
    { name: "lumina-forge:inventory-draft" },
  ),
);
