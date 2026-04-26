import passiveEffectsTable from "./passive-effects-table.json";
import pictoTable from "./picto-table.json";
import weaponTable from "./weapon-table.json";
import type { Inventory } from "@/types/api";
import { emptyInventory } from "@/types/api";

interface WeaponEntry {
  display: string;
  character: string;
}

const WEAPONS = weaponTable as Record<string, WeaponEntry>;
const PICTOS = pictoTable as Record<string, string>;

/**
 * Convert PascalCase / Title Case name to our kebab-case vault slug.
 * "BreakingAttack" → "breaking-attack"
 * "Full Strength" → "full-strength"
 */
export function slugify(name: string): string {
  return name
    .replace(/([a-z])([A-Z])/g, "$1-$2")
    .replace(/[^A-Za-z0-9]+/g, "-")
    .toLowerCase()
    .replace(/^-+|-+$/g, "");
}

/**
 * The save stores picto/lumina entries by their internal RowName
 * (e.g. "Stand"). Up to three lookup tables can resolve them:
 *
 *   1. ST_PassiveEffects — the string table for picto/lumina display
 *      names. Built from `PASSIVE_<RowName>_Name` keys.
 *   2. DT_jRPG_Items_Composite — the broader item data table. Some
 *      pictos appear under different RowNames here (e.g. ``InitialAp+1A``)
 *      that the passive table doesn't carry.
 *   3. Raw slugify, as a last resort.
 *
 * Trying both tables makes the importer resilient to E33's two
 * naming conventions (with-`+`, with-`_`).
 */
export function passiveSlug(saveName: string): string {
  const st = passiveEffectsTable as Record<string, string>;
  if (st[saveName]) return slugify(st[saveName]);
  if (PICTOS[saveName]) return slugify(PICTOS[saveName]);
  return slugify(saveName);
}

/**
 * Weapons are stored under their *internal* hardcoded names — usually
 * the same as the display name ("Gaulteram") but sometimes renamed:
 * the save says ``Sirenim_1`` for what the player actually sees as
 * "Choralim". DT_jRPG_Items_Composite gives the canonical mapping for
 * all 128 weapons.
 */
export function weaponSlug(saveName: string): string {
  const entry = WEAPONS[saveName];
  if (entry) return slugify(entry.display);
  return slugify(saveName);
}

/** Picto hardcoded → display via DT_jRPG_Items_Composite (230 entries). */
export function pictoSlug(saveName: string): string {
  const display = PICTOS[saveName];
  if (display) return slugify(display);
  // Fall back to the passive-effects table (some pictos share a
  // RowName there) and finally to a raw slugify.
  return passiveSlug(saveName);
}

/**
 * Skills come with a per-character suffix (``Combo1_Gustave``,
 * ``MarkingShot_Gustave``). After stripping, some hardcoded names still
 * differ from Fextralife's display ("UnleashCharge" → Overcharge,
 * "Combo1" → Lumière Assault). The override map handles the deltas;
 * everything else falls through to plain slugify.
 */
// Skills whose save-internal name doesn't match Fextralife's slug.
// Two patterns:
//   1. Renames — the in-game text is different from the wiki text
//      (UnleashCharge → Overcharge, Combo1 → Lumière Assault).
//   2. Slug-shape mismatches — Fextralife collapses some PascalCase
//      names to single-word slugs (RockSlide → rockslide instead of
//      rock-slide). Slugify always produces hyphens, so map back.
//
// Skills not on Fextralife (IceGust, Earthquake, ThermalTransfer…)
// land in the inventory as their slugified form and the optimizer
// reports them as unknown. Adding them as vault stubs is future work.
const SKILL_NAME_OVERRIDES: Record<string, string> = {
  combo1: "lumiere-assault",
  "unleash-charge": "overcharge",
  "perfect-recovery": "recovery",
  "rock-slide": "rockslide",
  "terra-quake": "terraquake",
  "thunder-fall": "thunderfall",
};

export function skillSlug(saveName: string): string {
  const stripped = saveName.replace(
    /_(Gustave|Lune|Maelle|Sciel|Verso|Monoco|Frey)$/i,
    "",
  );
  const slug = slugify(stripped);
  return SKILL_NAME_OVERRIDES[slug] ?? slug;
}

export interface ParsedCharacter {
  hardcodedName: string;
  level: number;
  attributes: Inventory["attributes"];
  weapon: string | null;
  pictoSlots: string[]; // ItemType=NewEnumerator0 in EquippedItemsPerSlot
  passiveEffects: string[]; // EquippedPassiveEffects array
  unlockedSkills: string[]; // UnlockedSkills array
}

export interface ParsedSave {
  characters: ParsedCharacter[];
  // All weapons the player owns, keyed by hardcoded save name. The
  // frontend filters this by the chosen character at inventory-build
  // time.
  ownedWeapons: string[];
  // All pictos the player owns, in slug form. Pictos aren't
  // character-bound in-game, so this maps directly to
  // ``inventory.pictos_available``.
  ownedPictos: string[];
}

/**
 * Walk the JSON Save dump produced by ``read_save_as_json`` and return
 * one summary per character + the global inventory. The frontend asks
 * the user which character to import.
 */
export function parseSave(saveJson: unknown): ParsedSave {
  const root = (saveJson as { root?: { properties?: Record<string, unknown> } })?.root;
  if (!root?.properties) return { characters: [], ownedWeapons: [], ownedPictos: [] };

  const characters: ParsedCharacter[] = [];
  const collection = findKey(root.properties, /^CharactersCollection_\d+$/);
  const entries = ((collection as { Map?: unknown[] })?.Map ?? []) as Array<{
    key?: unknown;
    value?: unknown;
  }>;
  for (const entry of entries) {
    const name = readName(entry.key);
    const inner = readStructInner(entry.value);
    if (!name || !inner) continue;
    characters.push({
      hardcodedName: name,
      level: readInt(inner, /^CurrentLevel_/) ?? 1,
      attributes: readAttributes(inner),
      weapon: readEquippedWeapon(inner),
      pictoSlots: readEquippedPictos(inner),
      passiveEffects: readEquippedPassives(inner),
      unlockedSkills: readUnlockedSkills(inner),
    });
  }

  return {
    characters,
    ownedWeapons: readOwnedItemNames(root.properties).filter((n) => WEAPONS[n] !== undefined),
    ownedPictos: readOwnedItemNames(root.properties).filter((n) => PICTOS[n] !== undefined),
  };
}

function readOwnedItemNames(properties: Record<string, unknown>): string[] {
  const node = findKey(properties, /^InventoryItems_\d+$/) as
    | { Map?: Array<{ key?: unknown; value?: unknown }> }
    | undefined;
  if (!node?.Map) return [];
  const out: string[] = [];
  for (const e of node.Map) {
    const name = (e.key as { Name?: string })?.Name;
    if (typeof name === "string") out.push(name);
  }
  return out;
}

// E33 stores Gustave under the internal name "Frey" (his original name in
// the dev's pre-launch builds). Other characters happen to ship under
// their public names; we still go through this map so future renames
// land in one place.
const CHARACTER_NAME_OVERRIDES: Record<string, string> = {
  frey: "gustave",
};

function characterSlug(hardcodedName: string): string {
  const raw = slugify(hardcodedName);
  return CHARACTER_NAME_OVERRIDES[raw] ?? raw;
}

/**
 * Build an Inventory draft from a parsed character + the save's global
 * inventory list. Character names map through the override table so
 * the save's "Frey" lands on our "gustave" slug.
 *
 * Compared to v0.8.x: ``weapons_available`` now includes *all* weapons
 * the player owns for this character (filtered from the global
 * InventoryItems map), not just the equipped one. ``pictos_available``
 * is the union of every owned picto + everything the player has seen
 * via passive effects.
 */
export function characterToInventory(
  char: ParsedCharacter,
  saved: ParsedSave,
): Inventory {
  const inv = emptyInventory(characterSlug(char.hardcodedName));
  inv.level = char.level;
  inv.attributes = char.attributes;

  // All weapons the inventory says the player owns, filtered to the
  // chosen character. The save's hardcodedName is the player-facing
  // character ("Frey" → Gustave), but DT_jRPG_Items_Composite uses the
  // dev's internal name ("Noah" → Gustave). Match by the entry's
  // .character against either alias.
  const charPlayer = char.hardcodedName === "Frey" ? "Gustave" : char.hardcodedName;
  const charInternal = char.hardcodedName === "Frey" ? "Noah" : char.hardcodedName;
  const weaponSlugs = new Set<string>();
  if (char.weapon) weaponSlugs.add(char.weapon);
  for (const name of saved.ownedWeapons) {
    const entry = WEAPONS[name];
    if (!entry) continue;
    if (entry.character === charPlayer || entry.character === charInternal) {
      weaponSlugs.add(slugify(entry.display));
    }
  }
  inv.weapons_available = Array.from(weaponSlugs).sort();

  // Pictos: union of (every picto in inventory) + (passive effects
  // recorded on the character) + (the three equipped slot pictos).
  const pictoSlugs = new Set<string>();
  for (const name of saved.ownedPictos) {
    pictoSlugs.add(pictoSlug(name));
  }
  for (const s of char.passiveEffects) pictoSlugs.add(s);
  for (const s of char.pictoSlots) pictoSlugs.add(s);
  inv.pictos_available = Array.from(pictoSlugs).sort();

  // Mastered pictos = the three equipped slots. Luminas_extra =
  // anything in passive effects not already mastered.
  inv.pictos_mastered = char.pictoSlots;
  inv.luminas_extra = char.passiveEffects.filter(
    (s) => !char.pictoSlots.includes(s),
  );
  inv.skills_known = char.unlockedSkills;
  return inv;
}

// --- internals -------------------------------------------------------------

function findKey(record: Record<string, unknown>, pattern: RegExp): unknown {
  for (const [key, value] of Object.entries(record)) {
    if (pattern.test(key)) return value;
  }
  return undefined;
}

function readName(node: unknown): string | null {
  const n = (node as { Name?: string })?.Name;
  return typeof n === "string" ? n : null;
}

function readStructInner(node: unknown): Record<string, unknown> | null {
  // Shape: { Struct: { Struct: { <fields> } } } in uesave's serialised form.
  const a = (node as { Struct?: unknown })?.Struct;
  const b = (a as { Struct?: unknown })?.Struct;
  return (b as Record<string, unknown>) ?? null;
}

function readInt(record: Record<string, unknown>, pattern: RegExp): number | null {
  for (const [key, value] of Object.entries(record)) {
    if (pattern.test(key)) {
      const n = (value as { Int?: number })?.Int;
      return typeof n === "number" ? n : null;
    }
  }
  return null;
}

const ATTRIBUTE_BY_ENUM: Record<string, keyof Inventory["attributes"]> = {
  "ECharacterAttribute::NewEnumerator0": "vitality",
  "ECharacterAttribute::NewEnumerator1": "might",
  "ECharacterAttribute::NewEnumerator2": "defense",
  "ECharacterAttribute::NewEnumerator3": "agility",
  "ECharacterAttribute::NewEnumerator4": "luck",
};

function readAttributes(record: Record<string, unknown>): Inventory["attributes"] {
  const out = { might: 0, agility: 0, defense: 0, luck: 0, vitality: 0 };
  const node = findKey(record, /^AssignedAttributePoints_/) as
    | { Map?: Array<{ key?: unknown; value?: unknown }> }
    | undefined;
  if (!node?.Map) return out;
  for (const entry of node.Map) {
    const labelNode = (entry.key as { Byte?: { Label?: string } })?.Byte;
    const label = labelNode?.Label;
    if (!label) continue;
    const attr = ATTRIBUTE_BY_ENUM[label];
    if (!attr) continue;
    const v = (entry.value as { Int?: number })?.Int ?? 0;
    out[attr] = v;
  }
  return out;
}

function slotItemType(key: unknown): string | null {
  // Map keys have shape { Struct: { Struct: { ItemType_..., SlotIndex_... } } }
  const inner = ((key as { Struct?: { Struct?: Record<string, unknown> } })?.Struct
    ?.Struct) as Record<string, unknown> | undefined;
  if (!inner) return null;
  const entry = Object.entries(inner).find(([k]) => k.startsWith("ItemType_"))?.[1] as
    | { Byte?: { Label?: string } }
    | undefined;
  return entry?.Byte?.Label ?? null;
}

function equippedSlotsByType(
  record: Record<string, unknown>,
  itemTypeEnum: string,
  toSlug: (saveName: string) => string,
): string[] {
  const node = findKey(record, /^EquippedItemsPerSlot_/) as
    | { Map?: Array<{ key?: unknown; value?: unknown }> }
    | undefined;
  if (!node?.Map) return [];
  const out: string[] = [];
  for (const entry of node.Map) {
    if (slotItemType(entry.key) !== itemTypeEnum) continue;
    const value = (entry.value as { Name?: string })?.Name;
    if (typeof value === "string") out.push(toSlug(value));
  }
  return Array.from(new Set(out));
}

function readEquippedWeapon(record: Record<string, unknown>): string | null {
  // ItemType = NewEnumerator0 → weapon slot. Weapons go through the
  // dedicated weapon table so internal aliases (Sirenim_1 → Choralim)
  // resolve correctly.
  return equippedSlotsByType(record, "E_jRPG_ItemType::NewEnumerator0", weaponSlug)[0] ?? null;
}

function readEquippedPictos(record: Record<string, unknown>): string[] {
  return equippedSlotsByType(record, "E_jRPG_ItemType::NewEnumerator10", passiveSlug);
}

function readUnlockedSkills(record: Record<string, unknown>): string[] {
  const node = findKey(record, /^UnlockedSkills_/) as
    | { Array?: { Base?: { Name?: string[] } } }
    | undefined;
  const names = node?.Array?.Base?.Name ?? [];
  return Array.from(new Set(names.map((n) => skillSlug(n))));
}

function readEquippedPassives(record: Record<string, unknown>): string[] {
  const node = findKey(record, /^EquippedPassiveEffects_/) as
    | { Array?: { Base?: { Name?: string[] } } }
    | undefined;
  const names = node?.Array?.Base?.Name ?? [];
  return names.map((n) => passiveSlug(n));
}
