import { Download, RefreshCw, Upload } from "lucide-react";
import * as React from "react";

import { useVaultItems } from "@/api/hooks";
import { MultiSelectList } from "@/components/MultiSelectList";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useInventoryStore } from "@/stores/inventory";
import type { Inventory, VaultItem } from "@/types/api";
import { emptyInventory } from "@/types/api";

const ATTRIBUTE_KEYS: ReadonlyArray<keyof Inventory["attributes"]> = [
  "might",
  "agility",
  "defense",
  "luck",
  "vitality",
];

export function InventoryForm() {
  const draft = useInventoryStore((s) => s.draft);
  const setDraft = useInventoryStore((s) => s.setDraft);
  const setCharacter = useInventoryStore((s) => s.setCharacter);
  const patch = useInventoryStore((s) => s.patch);
  const reset = useInventoryStore((s) => s.reset);

  const characters = useVaultItems("character");
  const weapons = useVaultItems("weapon", draft.character);
  const pictos = useVaultItems("picto");
  const luminas = useVaultItems("lumina");
  const skills = useVaultItems("skill", draft.character);

  const masteredDisabled = React.useCallback(
    (item: VaultItem) => !draft.pictos_available.includes(item.slug),
    [draft.pictos_available],
  );

  function handlePicto(slugs: string[]) {
    patch({
      pictos_available: slugs,
      // keep mastered subset consistent with available
      pictos_mastered: draft.pictos_mastered.filter((s) => slugs.includes(s)),
    });
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(draft, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `inventory-${draft.character}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function importJson(ev: React.ChangeEvent<HTMLInputElement>) {
    const file = ev.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      const parsed = JSON.parse(text) as Inventory;
      setDraft({ ...emptyInventory(parsed.character ?? "gustave"), ...parsed });
    } catch (err) {
      alert(`Invalid JSON: ${(err as Error).message}`);
    } finally {
      ev.target.value = "";
    }
  }

  const pictoMeta = React.useCallback(
    (item: VaultItem) => (item.pp_cost != null ? `PP ${item.pp_cost}` : ""),
    [],
  );
  const weaponMeta = React.useCallback(
    (item: VaultItem) => (item.base_damage != null ? `⚔ ${item.base_damage}` : ""),
    [],
  );
  const skillMeta = React.useCallback(
    (item: VaultItem) => (item.ap_cost != null ? `AP ${item.ap_cost}` : ""),
    [],
  );

  return (
    <div className="grid gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Character & attributes</CardTitle>
          <div className="flex items-center gap-2">
            <label className="cursor-pointer">
              <input type="file" accept="application/json" className="hidden" onChange={importJson} />
              <span className="inline-flex h-9 items-center gap-1.5 rounded-md border border-input bg-background px-3 text-sm font-medium hover:bg-accent">
                <Upload className="h-3.5 w-3.5" />
                Import JSON
              </span>
            </label>
            <Button variant="outline" size="sm" onClick={exportJson}>
              <Download className="h-3.5 w-3.5" />
              Export JSON
            </Button>
            <Button variant="ghost" size="sm" onClick={() => reset(draft.character)}>
              <RefreshCw className="h-3.5 w-3.5" />
              Clear
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label>Character</Label>
            <Select value={draft.character} onValueChange={setCharacter}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a character" />
              </SelectTrigger>
              <SelectContent>
                {(characters.data?.items ?? []).map((c) => (
                  <SelectItem key={c.slug} value={c.slug}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="level">Level</Label>
            <Input
              id="level"
              type="number"
              min={1}
              value={draft.level}
              onChange={(e) => patch({ level: Number(e.target.value) || 1 })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="pp_budget">PP budget</Label>
            <Input
              id="pp_budget"
              type="number"
              min={0}
              value={draft.pp_budget}
              onChange={(e) => patch({ pp_budget: Number(e.target.value) || 0 })}
            />
          </div>
          {ATTRIBUTE_KEYS.map((key) => (
            <div key={key} className="space-y-2">
              <Label htmlFor={`attr-${key}`} className="capitalize">
                {key}
              </Label>
              <Input
                id={`attr-${key}`}
                type="number"
                min={0}
                value={draft.attributes[key]}
                onChange={(e) =>
                  patch({
                    attributes: {
                      ...draft.attributes,
                      [key]: Number(e.target.value) || 0,
                    },
                  })
                }
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Weapons available ({draft.character})</CardTitle>
        </CardHeader>
        <CardContent>
          <MultiSelectList
            items={weapons.data?.items ?? []}
            value={draft.weapons_available}
            onChange={(weapons_available) => patch({ weapons_available })}
            renderMeta={weaponMeta}
            placeholder="Search weapons…"
            emptyMessage="No weapons for this character."
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pictos available</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <Label className="mb-2 block text-xs text-muted-foreground">
              All pictos you own
            </Label>
            <MultiSelectList
              items={pictos.data?.items ?? []}
              value={draft.pictos_available}
              onChange={handlePicto}
              renderMeta={pictoMeta}
              placeholder="Search pictos…"
            />
          </div>
          <div>
            <Label className="mb-2 block text-xs text-muted-foreground">
              Mastered (unlocks the lumina form)
            </Label>
            <MultiSelectList
              items={(pictos.data?.items ?? []).filter((p) =>
                draft.pictos_available.includes(p.slug),
              )}
              value={draft.pictos_mastered}
              onChange={(pictos_mastered) => patch({ pictos_mastered })}
              disabled={masteredDisabled}
              placeholder="Search mastered pictos…"
              emptyMessage="Mark pictos available on the left first."
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Luminas (extra — on top of mastered pictos)</CardTitle>
        </CardHeader>
        <CardContent>
          <MultiSelectList
            items={luminas.data?.items ?? []}
            value={draft.luminas_extra}
            onChange={(luminas_extra) => patch({ luminas_extra })}
            renderMeta={pictoMeta}
            placeholder="Search luminas…"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Skills known ({draft.character})</CardTitle>
        </CardHeader>
        <CardContent>
          <MultiSelectList
            items={skills.data?.items ?? []}
            value={draft.skills_known}
            onChange={(skills_known) => patch({ skills_known })}
            renderMeta={skillMeta}
            placeholder="Search skills…"
            emptyMessage="No skills for this character."
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>JSON preview</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            readOnly
            value={JSON.stringify(draft, null, 2)}
            className="h-48"
          />
        </CardContent>
      </Card>
    </div>
  );
}
