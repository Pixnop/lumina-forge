import { Link } from "@tanstack/react-router";
import { Wand2 } from "lucide-react";

import { useVaultInfo } from "@/api/hooks";
import { InventoryForm } from "@/components/InventoryForm";
import { Button } from "@/components/ui/button";

export function HomePage() {
  const info = useVaultInfo();
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
      <InventoryForm />
    </div>
  );
}
