import passiveEffectsTable from "./passive-effects-table.json";
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
 * name lands on our vault slug for ~90 % of items out of the box.
 */
export function passiveSlug(saveName: string): string {
  const table = passiveEffectsTable as Record<string, string>;
  const display = table[saveName];
  if (display) return slugify(display);
  // Fall back to raw PascalCase → kebab — works for items not in the
  // string table (some weapons use the same internal name as display).
  return slugify(saveName);
}

interface ParsedCharacter {
  hardcodedName: string;
  level: number;
  attributes: Inventory["attributes"];
  weapon: string | null;
  pictoSlots: string[]; // ItemType=NewEnumerator0 in EquippedItemsPerSlot
  passiveEffects: string[]; // EquippedPassiveEffects array
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
    });
  }
  return out;
}

/**
 * Build an Inventory draft from a parsed character. The character name
 * comes from the save's hardcoded name and is lowercased to match our
 * vault's character slugs (Gustave → gustave, Frey → frey, …).
 */
export function characterToInventory(char: ParsedCharacter): Inventory {
  const inv = emptyInventory(slugify(char.hardcodedName));
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

function readEquippedWeapon(record: Record<string, unknown>): string | null {
  // EquippedItemsPerSlot is a Map<FEquipmentSlot, NameProperty>.
  // FEquipmentSlot.ItemType = NewEnumerator0 → weapon (typically slot 0).
  const node = findKey(record, /^EquippedItemsPerSlot_/) as
    | { Map?: Array<{ key?: unknown; value?: unknown }> }
    | undefined;
  if (!node?.Map) return null;
  for (const entry of node.Map) {
    const slotInner = readStructInner({ Struct: entry.key });
    if (!slotInner) continue;
    const itemType = (
      Object.entries(slotInner).find(([k]) => k.startsWith("ItemType_"))?.[1] as
        | { Byte?: { Label?: string } }
        | undefined
    )?.Byte?.Label;
    if (itemType !== "E_jRPG_ItemType::NewEnumerator0") continue;
    const value = (entry.value as { Name?: string })?.Name;
    if (typeof value === "string") return passiveSlug(value);
  }
  return null;
}

function readEquippedPictos(record: Record<string, unknown>): string[] {
  // ItemType = NewEnumerator10 in the few saves we've inspected → picto slots
  const node = findKey(record, /^EquippedItemsPerSlot_/) as
    | { Map?: Array<{ key?: unknown; value?: unknown }> }
    | undefined;
  if (!node?.Map) return [];
  const out: string[] = [];
  for (const entry of node.Map) {
    const slotInner = readStructInner({ Struct: entry.key });
    if (!slotInner) continue;
    const itemType = (
      Object.entries(slotInner).find(([k]) => k.startsWith("ItemType_"))?.[1] as
        | { Byte?: { Label?: string } }
        | undefined
    )?.Byte?.Label;
    if (itemType !== "E_jRPG_ItemType::NewEnumerator10") continue;
    const value = (entry.value as { Name?: string })?.Name;
    if (typeof value === "string") out.push(passiveSlug(value));
  }
  return Array.from(new Set(out));
}

function readEquippedPassives(record: Record<string, unknown>): string[] {
  const node = findKey(record, /^EquippedPassiveEffects_/) as
    | { Array?: { Base?: { Name?: string[] } } }
    | undefined;
  const names = node?.Array?.Base?.Name ?? [];
  return names.map((n) => passiveSlug(n));
}
