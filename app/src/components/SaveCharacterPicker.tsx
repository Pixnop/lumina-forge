import { Sword, X } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ParsedCharacter, ParsedSave } from "@/lib/save/importer";
import { characterToInventory } from "@/lib/save/importer";
import { useInventoryStore } from "@/stores/inventory";

interface Props {
  saved: ParsedSave;
  onDismiss: () => void;
}

/**
 * Lets the user pick which character from a freshly-imported save
 * should populate the inventory draft. Replaces the v0.8.x heuristic
 * that auto-picked the first equipped character (always Gustave/Frey
 * because of save order).
 */
export function SaveCharacterPicker({ saved, onDismiss }: Props) {
  const { t } = useTranslation();
  const setDraft = useInventoryStore((s) => s.setDraft);

  function pick(c: ParsedCharacter) {
    setDraft(characterToInventory(c, saved));
    onDismiss();
  }

  return (
    <Card className="border-primary/40 bg-primary/5">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-base">{t("home.import_pick_title")}</CardTitle>
        <Button variant="ghost" size="sm" onClick={onDismiss}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
        {saved.characters.map((c) => {
          const totalItems =
            c.passiveEffects.length + c.pictoSlots.length + c.unlockedSkills.length;
          return (
            <button
              key={c.hardcodedName}
              onClick={() => pick(c)}
              className="rounded-md border border-border bg-card p-3 text-left transition hover:border-primary"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold">
                  {c.hardcodedName === "Frey" ? "Gustave" : c.hardcodedName}
                </span>
                <Badge variant="outline" className="text-xs">
                  {t("home.import_pick_level", { lvl: c.level })}
                </Badge>
              </div>
              <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                <Sword className="h-3 w-3" />
                <span className="truncate">{c.weapon ?? "—"}</span>
              </div>
              <div className="mt-1 flex flex-wrap gap-1 text-xs text-muted-foreground">
                <Badge variant="secondary" className="text-[0.65rem]">
                  {t("home.import_pick_pictos", { n: c.pictoSlots.length })}
                </Badge>
                <Badge variant="secondary" className="text-[0.65rem]">
                  {t("home.import_pick_passives", { n: c.passiveEffects.length })}
                </Badge>
                <Badge variant="secondary" className="text-[0.65rem]">
                  {t("home.import_pick_skills", { n: c.unlockedSkills.length })}
                </Badge>
                {totalItems === 0 && (
                  <span className="italic">{t("home.import_pick_unequipped")}</span>
                )}
              </div>
            </button>
          );
        })}
      </CardContent>
    </Card>
  );
}
