// Wire types — match packages/optimizer/src/optimizer/api/schemas.py.

export type Mode = "dps" | "utility" | "balanced";

export interface Attributes {
  might: number;
  agility: number;
  defense: number;
  luck: number;
  vitality: number;
}

export interface Inventory {
  character: string;
  level: number;
  attributes: Attributes;
  weapons_available: string[];
  pictos_available: string[];
  pictos_mastered: string[];
  luminas_extra: string[];
  pp_budget: number;
  skills_known: string[];
}

export interface DamageEstimate {
  base: number;
  might_mult: number;
  picto_mult: number;
  lumina_mult: number;
  crit_mult: number;
  synergy_mult: number;
  ap_mult: number;
  est_dps: number;
  raw_dps: number;
}

export interface WeaponAlternative {
  weapon: string;
  est_dps: number;
  raw_dps: number;
}

export interface UtilityScore {
  has_revive: boolean;
  has_heal: boolean;
  has_defense_buff: boolean;
  score_0_1: number;
}

export interface BuildLoadout {
  character: string;
  weapon: string;
  pictos: string[];
  luminas: string[];
  skills_used: string[];
}

export type DpsTier = "S" | "A" | "B" | "C" | "D";

export interface ArchetypeMatch {
  slug: string;
  name: string;
  archetype?: string | null;
  dps_tier?: DpsTier | null;
  confidence: "exact" | "variant";
  bonus_applied: number;
}

export interface AspirationalBuild {
  slug: string;
  name: string;
  character?: string | null;
  archetype?: string | null;
  dps_tier?: DpsTier | null;
  missing_pictos: string[];
  missing_luminas: string[];
  missing_weapon?: string | null;
  missing_skills: string[];
}

export interface RankedBuildResponse {
  rank: number;
  total_score: number;
  loadout: BuildLoadout;
  damage: DamageEstimate;
  utility: UtilityScore;
  synergies_matched: string[];
  rotation_hint: string[];
  why: string[];
  weapon_alternatives: WeaponAlternative[];
  archetype?: ArchetypeMatch | null;
}

export interface OptimizeRequest {
  inventory: Inventory;
  top?: number;
  mode?: Mode;
  weight_utility?: number | null;
}

export interface OptimizeResponse {
  builds: RankedBuildResponse[];
  aspirational: AspirationalBuild[];
  total_enumerated?: number | null;
}

export interface VaultItem {
  slug: string;
  name: string;
  category?: string | null;
  character?: string | null;
  pp_cost?: number | null;
  ap_cost?: number | null;
  base_damage?: number | null;
}

export interface VaultItemsResponse {
  items: VaultItem[];
}

export interface VaultInfoResponse {
  characters: number;
  pictos: number;
  weapons: number;
  luminas: number;
  skills: number;
  synergies: number;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export type VaultItemType = "character" | "picto" | "weapon" | "lumina" | "skill";

export function emptyInventory(character: string): Inventory {
  return {
    character,
    level: 1,
    attributes: { might: 0, agility: 0, defense: 0, luck: 0, vitality: 0 },
    weapons_available: [],
    pictos_available: [],
    pictos_mastered: [],
    luminas_extra: [],
    pp_budget: 0,
    skills_known: [],
  };
}
