import { Link } from "@tanstack/react-router";
import { Sparkles, Wand2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useVaultInfo } from "@/api/hooks";
import { InventoryForm } from "@/components/InventoryForm";
import { InventoryLibrary } from "@/components/InventoryLibrary";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GUSTAVE_EXAMPLE } from "@/lib/examples";
import { useInventoryStore } from "@/stores/inventory";

export function HomePage() {
  const { t } = useTranslation();
  const info = useVaultInfo();
  const draft = useInventoryStore((s) => s.draft);
  const setDraft = useInventoryStore((s) => s.setDraft);

  const isEmpty =
    draft.weapons_available.length === 0 && draft.pictos_available.length === 0;

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
        <Button asChild>
          <Link to="/optimize">
            <Wand2 className="h-4 w-4" />
            {t("home.optimize")}
          </Link>
        </Button>
      </div>

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
