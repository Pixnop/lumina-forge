import { Link } from "@tanstack/react-router";
import { Sparkles, Wand2 } from "lucide-react";

import { useVaultInfo } from "@/api/hooks";
import { InventoryForm } from "@/components/InventoryForm";
import { InventoryLibrary } from "@/components/InventoryLibrary";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GUSTAVE_EXAMPLE } from "@/lib/examples";
import { useInventoryStore } from "@/stores/inventory";

export function HomePage() {
  const info = useVaultInfo();
  const draft = useInventoryStore((s) => s.draft);
  const setDraft = useInventoryStore((s) => s.setDraft);

  const isEmpty =
    draft.weapons_available.length === 0 && draft.pictos_available.length === 0;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Inventory</h1>
          <p className="text-sm text-muted-foreground">
            Tell the optimizer what you currently own. Everything auto-saves to
            localStorage — export to JSON for sharing.
          </p>
          {info.data ? (
            <p className="mt-1 text-xs text-muted-foreground">
              Vault loaded — {info.data.pictos} pictos, {info.data.weapons} weapons,{" "}
              {info.data.luminas} luminas, {info.data.skills} skills.
            </p>
          ) : null}
        </div>
        <Button asChild>
          <Link to="/optimize">
            <Wand2 className="h-4 w-4" />
            Optimize
          </Link>
        </Button>
      </div>

      {isEmpty && (
        <Card className="border-primary/40 bg-primary/5">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-primary" />
              First time here?
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 pt-0 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              Load a starter Gustave inventory (3 weapons, 10 pictos, 2 mastered)
              to see the optimizer in action right away.
            </p>
            <Button variant="outline" onClick={() => setDraft(GUSTAVE_EXAMPLE)}>
              Load Gustave example
            </Button>
          </CardContent>
        </Card>
      )}

      <InventoryLibrary />

      <InventoryForm />
    </div>
  );
}
