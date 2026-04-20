import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Inventory } from "@/types/api";

export interface SavedInventory {
  id: string;
  name: string;
  character: string;
  createdAt: number;
  updatedAt: number;
  inventory: Inventory;
}

interface LibraryState {
  items: SavedInventory[];
  save: (name: string, inventory: Inventory) => SavedInventory;
  update: (id: string, inventory: Inventory) => void;
  rename: (id: string, name: string) => void;
  remove: (id: string) => void;
  duplicate: (id: string) => SavedInventory | undefined;
  get: (id: string) => SavedInventory | undefined;
}

function newId(): string {
  // Crypto-free, good enough for localstorage identity.
  return `inv_${Math.random().toString(36).slice(2, 10)}_${Date.now().toString(36)}`;
}

export const useLibraryStore = create<LibraryState>()(
  persist(
    (set, get) => ({
      items: [],
      save: (name, inventory) => {
        const now = Date.now();
        const saved: SavedInventory = {
          id: newId(),
          name: name.trim() || `${inventory.character} — ${new Date(now).toLocaleString()}`,
          character: inventory.character,
          createdAt: now,
          updatedAt: now,
          inventory: structuredClone(inventory),
        };
        set((state) => ({ items: [saved, ...state.items] }));
        return saved;
      },
      update: (id, inventory) =>
        set((state) => ({
          items: state.items.map((item) =>
            item.id === id
              ? {
                  ...item,
                  inventory: structuredClone(inventory),
                  character: inventory.character,
                  updatedAt: Date.now(),
                }
              : item,
          ),
        })),
      rename: (id, name) =>
        set((state) => ({
          items: state.items.map((item) =>
            item.id === id ? { ...item, name, updatedAt: Date.now() } : item,
          ),
        })),
      remove: (id) =>
        set((state) => ({ items: state.items.filter((item) => item.id !== id) })),
      duplicate: (id) => {
        const source = get().items.find((item) => item.id === id);
        if (!source) return undefined;
        return get().save(`${source.name} (copy)`, source.inventory);
      },
      get: (id) => get().items.find((item) => item.id === id),
    }),
    { name: "lumina-forge:inventory-library" },
  ),
);
