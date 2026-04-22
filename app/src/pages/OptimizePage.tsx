import { Link, useNavigate } from "@tanstack/react-router";
import { AlertCircle, ArrowLeft, Loader2, Wand2 } from "lucide-react";
import * as React from "react";

import { useOptimize } from "@/api/hooks";
import { AspirationalList } from "@/components/AspirationalList";
import { BuildCard } from "@/components/BuildCard";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useInventoryStore } from "@/stores/inventory";
import { useResultsStore } from "@/stores/results";
import type { Mode } from "@/types/api";

const MODES: { value: Mode; label: string }[] = [
  { value: "dps", label: "DPS" },
  { value: "balanced", label: "Balanced" },
  { value: "utility", label: "Utility" },
];

export function OptimizePage() {
  const draft = useInventoryStore((s) => s.draft);
  const setResults = useResultsStore((s) => s.setResults);
  const navigate = useNavigate();
  const [mode, setMode] = React.useState<Mode>("dps");
  const [top, setTop] = React.useState(5);
  const mutation = useOptimize();

  function run() {
    mutation.mutate(
      { inventory: draft, mode, top },
      { onSuccess: (data) => setResults(data) },
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Link to="/" className="inline-flex items-center gap-1 hover:text-foreground">
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to inventory
            </Link>
          </div>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">Optimize</h1>
          <p className="text-sm text-muted-foreground">
            Character: <span className="font-semibold">{draft.character}</span> —{" "}
            {draft.weapons_available.length} weapons,{" "}
            {draft.pictos_available.length} pictos, PP budget {draft.pp_budget}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={mode} onValueChange={(v) => setMode(v as Mode)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MODES.map((m) => (
                <SelectItem key={m.value} value={m.value}>
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={String(top)} onValueChange={(v) => setTop(Number(v))}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[3, 5, 10, 20].map((n) => (
                <SelectItem key={n} value={String(n)}>
                  Top {n}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={run} disabled={mutation.isPending}>
            {mutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Wand2 className="h-4 w-4" />
            )}
            Run
          </Button>
        </div>
      </div>

      {mutation.isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive bg-destructive/10 px-3 py-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          {(mutation.error as Error).message}
        </div>
      )}

      {mutation.isPending && (
        <div className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-border py-12 text-sm text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin" />
          Enumerating combinations…
        </div>
      )}

      {mutation.data && mutation.data.builds.length === 0 && (
        <div className="rounded-md border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
          No build could be assembled. Check that you have at least one compatible
          weapon and 3 pictos.
        </div>
      )}

      {mutation.data && mutation.data.builds.length > 0 && (
        <>
          <div className="grid gap-3 md:grid-cols-2">
            {mutation.data.builds.map((b) => (
              <BuildCard
                key={b.rank}
                rank={b.rank}
                build={b}
                onClick={() =>
                  navigate({
                    to: "/builds/$rank",
                    params: { rank: String(b.rank) },
                  })
                }
              />
            ))}
          </div>
          {mutation.data.aspirational && mutation.data.aspirational.length > 0 && (
            <AspirationalList aspirational={mutation.data.aspirational} />
          )}
        </>
      )}

      {!mutation.data && !mutation.isPending && (
        <div className="rounded-md border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
          Click <span className="font-semibold">Run</span> to rank builds from your inventory.
        </div>
      )}
    </div>
  );
}
