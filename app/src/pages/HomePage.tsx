import { Link } from "@tanstack/react-router";
import { invoke } from "@tauri-apps/api/core";
import { localDataDir } from "@tauri-apps/api/path";
import { open } from "@tauri-apps/plugin-dialog";
import { FileUp, Sparkles, Wand2 } from "lucide-react";
import * as React from "react";
import { useTranslation } from "react-i18next";

import { useVaultInfo } from "@/api/hooks";
import { InventoryForm } from "@/components/InventoryForm";
import { InventoryLibrary } from "@/components/InventoryLibrary";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GUSTAVE_EXAMPLE } from "@/lib/examples";
import { characterToInventory, parseSave } from "@/lib/save/importer";
import { useInventoryStore } from "@/stores/inventory";

export function HomePage() {
  const { t } = useTranslation();
  const info = useVaultInfo();
  const draft = useInventoryStore((s) => s.draft);
  const setDraft = useInventoryStore((s) => s.setDraft);
  const [importError, setImportError] = React.useState<string | null>(null);

  const isEmpty =
    draft.weapons_available.length === 0 && draft.pictos_available.length === 0;

  async function importSave() {
    setImportError(null);
    try {
      // Default to E33's typical save dir on Windows:
      //   %LOCALAPPDATA%\Sandfall\Saved\SaveGames
      // localDataDir() resolves the platform's local-data root (Windows
      // %LOCALAPPDATA%, macOS ~/Library/Application Support, Linux
      // ~/.local/share). Best-effort — fall back to no defaultPath if
      // anything throws.
      let defaultPath: string | undefined;
      try {
        const root = await localDataDir();
        defaultPath = `${root}/Sandfall/Saved/SaveGames`.replace(/\\/g, "/");
      } catch {
        defaultPath = undefined;
      }

      const path = await open({
        multiple: false,
        defaultPath,
        filters: [{ name: "Save", extensions: ["sav"] }],
      });
      if (typeof path !== "string") return;
      const json = await invoke<string>("read_save_as_json", { path });
      const parsed = parseSave(JSON.parse(json));
      const equipped = parsed.find((c) => c.weapon || c.passiveEffects.length > 0);
      if (!equipped) {
        setImportError(t("home.import_save_empty"));
        return;
      }
      setDraft(characterToInventory(equipped));
    } catch (err) {
      setImportError(
        t("home.import_save_failed", { error: (err as Error).message ?? String(err) }),
      );
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t("home.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("home.subtitle")}</p>
          {info.data ? (
            <p className="mt-1 text-xs text-muted-foreground">
              {t("home.vault_loaded", {
                pictos: info.data.pictos,
                weapons: info.data.weapons,
                luminas: info.data.luminas,
                skills: info.data.skills,
              })}
            </p>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={importSave} title={t("home.import_save_hint")}>
            <FileUp className="h-4 w-4" />
            {t("home.import_save")}
          </Button>
          <Button asChild>
            <Link to="/optimize">
              <Wand2 className="h-4 w-4" />
              {t("home.optimize")}
            </Link>
          </Button>
        </div>
      </div>

      {importError && (
        <div className="rounded-md border border-destructive bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {importError}
        </div>
      )}

      {isEmpty && (
        <Card className="border-primary/40 bg-primary/5">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-primary" />
              {t("home.first_time_title")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 pt-0 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">{t("home.first_time_hint")}</p>
            <Button variant="outline" onClick={() => setDraft(GUSTAVE_EXAMPLE)}>
              {t("home.load_example")}
            </Button>
          </CardContent>
        </Card>
      )}

      <InventoryLibrary />

      <InventoryForm />
    </div>
  );
}
