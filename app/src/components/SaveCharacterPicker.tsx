import { useNavigate } from "@tanstack/react-router";
import { Check, Sword, Users, X } from "lucide-react";
import * as React from "react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ParsedCharacter, ParsedSave } from "@/lib/save/importer";
import { characterToInventory } from "@/lib/save/importer";
import { useInventoryStore } from "@/stores/inventory";
import { useTeamStore } from "@/stores/team";

interface Props {
  saved: ParsedSave;
  onDismiss: () => void;
}

/**
 * After a save import, lets the player either pick a single character
 * (one-tap → fills the solo draft) or compose a 2-3 member party
 * (toggle each portrait → run team optimize). The two flows share the
 * same picker so the user doesn't have to re-import to switch modes.
 */
export function SaveCharacterPicker({ saved, onDismiss }: Props) {
  const { t } = useTranslation();
  const setDraft = useInventoryStore((s) => s.setDraft);
  const setTeamMembers = useTeamStore((s) => s.setMembers);
  const navigate = useNavigate();
  const [selected, setSelected] = React.useState<string[]>([]);

  function toggleSelect(name: string) {
    setSelected((prev) => {
      if (prev.includes(name)) return prev.filter((n) => n !== name);
      if (prev.length >= 3) return prev; // hard cap at 3
      return [...prev, name];
    });
  }

  function pickSolo(c: ParsedCharacter) {
    setDraft(characterToInventory(c, saved));
    onDismiss();
  }

  function runTeam() {
    const members = selected
      .map((name) => saved.characters.find((c) => c.hardcodedName === name))
      .filter((c): c is ParsedCharacter => c !== undefined)
      .map((c) => characterToInventory(c, saved));
    setTeamMembers(members);
    onDismiss();
    navigate({ to: "/team" });
  }

  return (
    <Card className="border-primary/40 bg-primary/5">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div>
          <CardTitle className="text-base">{t("home.import_pick_title")}</CardTitle>
          <p className="text-xs text-muted-foreground">
            {t("home.import_pick_hint")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selected.length >= 2 && (
            <Button size="sm" onClick={runTeam} className="gap-1">
              <Users className="h-3.5 w-3.5" />
              {t("home.import_run_team", { count: selected.length })}
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onDismiss}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
        {saved.characters.map((c) => {
          const display = c.hardcodedName === "Frey" ? "Gustave" : c.hardcodedName;
          const isSelected = selected.includes(c.hardcodedName);
          const totalItems =
            c.passiveEffects.length + c.pictoSlots.length + c.unlockedSkills.length;
          return (
            <div
              key={c.hardcodedName}
              className={`relative rounded-md border bg-card p-3 text-left transition ${
                isSelected
                  ? "border-primary ring-1 ring-primary"
                  : "border-border hover:border-primary"
              }`}
            >
              <button
                type="button"
                aria-label={t("home.import_toggle_select", { name: display })}
                onClick={() => toggleSelect(c.hardcodedName)}
                className={`absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full border ${
                  isSelected
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-background text-transparent hover:text-muted-foreground"
                }`}
              >
                <Check className="h-3 w-3" />
              </button>
              <button
                type="button"
                onClick={() => pickSolo(c)}
                className="block w-full text-left"
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{display}</span>
                  <Badge variant="outline" className="text-xs">
                    {t("home.import_pick_level", { lvl: c.level })}
                  </Badge>
                </div>
                <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                  <Sword className="h-3 w-3" />
                  <span className="truncate">
                    {c.weapon ?? "—"}
                    {c.weaponLevel != null && (
                      <span className="ml-1 text-[0.7rem]">(lvl {c.weaponLevel})</span>
                    )}
                  </span>
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
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
