import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Inventory, TeamOptimizeResponse } from "@/types/api";

interface TeamState {
  // 2 or 3 inventories — order matters; the API returns members keyed
  // by inventory_index so the UI knows which slot each build belongs to.
  members: Inventory[];
  setMembers: (members: Inventory[]) => void;
  addMember: (inv: Inventory) => void;
  removeMember: (index: number) => void;
  results: TeamOptimizeResponse | undefined;
  setResults: (r: TeamOptimizeResponse | undefined) => void;
  /** Look up a (team rank, member slot) pair for the build-detail page. */
  findMember: (rank: number, slot: number) =>
    | { build: TeamOptimizeResponse["teams"][number]["members"][number]["build"]; characterSlug: string }
    | undefined;
  clear: () => void;
}

export const useTeamStore = create<TeamState>()(
  persist(
    (set, get) => ({
      members: [],
      results: undefined,
      setMembers: (members) => set({ members, results: undefined }),
      addMember: (inv) => {
        const current = get().members;
        if (current.length >= 3) return;
        if (current.some((m) => m.character === inv.character)) return;
        set({ members: [...current, inv], results: undefined });
      },
      removeMember: (index) =>
        set((state) => ({
          members: state.members.filter((_, i) => i !== index),
          results: undefined,
        })),
      setResults: (r) => set({ results: r }),
      findMember: (rank, slot) => {
        const team = get().results?.teams[rank - 1];
        const member = team?.members[slot];
        if (!member) return undefined;
        const inv = get().members[member.inventory_index];
        return {
          build: member.build,
          characterSlug: inv?.character ?? `#${member.inventory_index}`,
        };
      },
      clear: () => set({ members: [], results: undefined }),
    }),
    { name: "lumina-forge:team-draft" },
  ),
);
