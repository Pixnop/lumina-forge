import passiveEffectsTable from "./passive-effects-table.json";
import weaponTable from "./weapon-table.json";
import type { Inventory } from "@/types/api";
import { emptyInventory } from "@/types/api";

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
 * (e.g. "Stand"). The Infarctus mapping table translates that to the
 * user-visible display name ("Full Strength"). Slugifying the display
 * name lands on our vault slug for ~100 % of items now that the missing
 * stubs are populated.
 */
export function passiveSlug(saveName: string): string {
  const table = passiveEffectsTable as Record<string, string>;
  const display = table[saveName];
  if (display) return slugify(display);
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
  const table = weaponTable as Record<string, string>;
  const display = table[saveName];
  if (display) return slugify(display);
  return slugify(saveName);
}

/**
 * Skills come with a per-character suffix (``Combo1_Gustave``,
 * ``MarkingShot_Gustave``). After stripping, some hardcoded names still
 * differ from Fextralife's display ("UnleashCharge" → Overcharge,
 * "Combo1" → Lumière Assault). The override map handles the deltas;
 * everything else falls through to plain slugify.
 */
const SKILL_NAME_OVERRIDES: Record<string, string> = {
  combo1: "lumiere-assault",
  "unleash-charge": "overcharge",
  "perfect-recovery": "recovery",
  // Lune
  rockslide: "rockslide",
  earthrising: "earth-rising",
  lightningdance: "lightning-dance",
  // Maelle
  swiftstride: "swift-stride",
  offensiveswitch: "offensive-switch",
  guarddown: "guard-down",
  fleuretfury: "fleuret-fury",
  mezzoforte: "mezzo-forte",
  // Sciel
  focusedforetell: "focused-foretell",
  sealedfate: "sealed-fate",
  markingcard: "marking-card",
  phantomblade: "phantom-blade",
  badomen: "bad-omen",
};

export function skillSlug(saveName: string): string {
  const stripped = saveName.replace(
    /_(Gustave|Lune|Maelle|Sciel|Verso|Monoco|Frey)$/i,
    "",
  );
  const slug = slugify(stripped);
  return SKILL_NAME_OVERRIDES[slug] ?? slug;
}

interface ParsedCharacter {
  hardcodedName: string;
  level: number;
  attributes: Inventory["attributes"];
  weapon: string | null;
  pictoSlots: string[]; // ItemType=NewEnumerator0 in EquippedItemsPerSlot
  passiveEffects: string[]; // EquippedPassiveEffects array
  unlockedSkills: string[]; // UnlockedSkills array
}

/**
 * Walk the JSON Save dump produced by ``read_save_as_json`` and return
 * one summary per character. The frontend then asks the user which
 * character to import.
 */
export function parseSave(saveJson: unknown): ParsedCharacter[] {
  const root = (saveJson as { root?: { properties?: Record<string, unknown> } })?.root;
  if (!root?.properties) return [];

  const collection = findKey(root.properties, /^CharactersCollection_\d+$/);
  if (!collection) return [];

  // Each entry: collection.Map[i] = { key: { Name: "Frey" }, value: { Struct: { Struct: { ... } } } }
  const entries = (collection as { Map?: unknown[] }).Map ?? [];
  const out: ParsedCharacter[] = [];
  for (const entry of entries as Array<{ key?: unknown; value?: unknown }>) {
    const name = readName(entry.key);
    const inner = readStructInner(entry.value);
    if (!name || !inner) continue;

    out.push({
      hardcodedName: name,
      level: readInt(inner, /^CurrentLevel_/) ?? 1,
      attributes: readAttributes(inner),
      weapon: readEquippedWeapon(inner),
      pictoSlots: readEquippedPictos(inner),
      passiveEffects: readEquippedPassives(inner),
      unlockedSkills: readUnlockedSkills(inner),
    });
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
 * Build an Inventory draft from a parsed character. Character names
 * map through the override table so the save's "Frey" lands on our
 * "gustave" slug.
 */
export function characterToInventory(char: ParsedCharacter): Inventory {
  const inv = emptyInventory(characterSlug(char.hardcodedName));
  inv.level = char.level;
  inv.attributes = char.attributes;
  if (char.weapon) inv.weapons_available = [char.weapon];

  // Pictos and luminas overlap in our vault — same slug, two roles.
  // The save splits them: EquippedItemsPerSlot[ItemType=0] are 3 picto
  // slots, EquippedPassiveEffects mixes pictos and luminas freely. We
  // treat the union as both pictos_available and luminas_extra, then
  // mark the slotted three as mastered so the optimizer can use their
  // lumina form.
  const allSlugs = Array.from(new Set([...char.pictoSlots, ...char.passiveEffects]));
  inv.pictos_available = allSlugs;
  inv.pictos_mastered = char.pictoSlots;
  inv.luminas_extra = char.passiveEffects.filter((s) => !char.pictoSlots.includes(s));
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
