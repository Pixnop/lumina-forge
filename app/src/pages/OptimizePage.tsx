import { Link, useNavigate } from "@tanstack/react-router";
import { AlertCircle, ArrowLeft, Loader2, Wand2 } from "lucide-react";
import * as React from "react";
import { useTranslation } from "react-i18next";

import { useOptimize } from "@/api/hooks";
import { AspirationalList } from "@/components/AspirationalList";
import { BuildCard } from "@/components/BuildCard";
import { OptimizeProgress } from "@/components/OptimizeProgress";
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

export function OptimizePage() {
  const { t } = useTranslation();
  const draft = useInventoryStore((s) => s.draft);
  const setResults = useResultsStore((s) => s.setResults);
  const navigate = useNavigate();
  const [mode, setMode] = React.useState<Mode>("dps");
  const [top, setTop] = React.useState(5);
  const mutation = useOptimize();

  const modes: { value: Mode; label: string }[] = [
    { value: "dps", label: t("optimize.mode.dps") },
    { value: "balanced", label: t("optimize.mode.balanced") },
    { value: "utility", label: t("optimize.mode.utility") },
  ];

  function run() {
    mutation.mutate(
      { inventory: draft, mode, top },
      { onSuccess: (data: typeof mutation.data) => data && setResults(data) },
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Link to="/" className="inline-flex items-center gap-1 hover:text-foreground">
              <ArrowLeft className="h-3.5 w-3.5" />
              {t("optimize.back")}
            </Link>
          </div>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">{t("optimize.title")}</h1>
          <p className="text-sm text-muted-foreground">
            {t("optimize.character")}: <span className="font-semibold">{draft.character}</span> —{" "}
            {t("optimize.inventory_summary", {
              weapons: draft.weapons_available.length,
              pictos: draft.pictos_available.length,
              pp: draft.pp_budget,
            })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={mode} onValueChange={(v) => setMode(v as Mode)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {modes.map((m) => (
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
                  {t("optimize.top", { count: n })}
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
            {t("optimize.run")}
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
        <OptimizeProgress
          pictosCount={draft.pictos_available.length}
          weaponsCount={draft.weapons_available.length}
          phase={mutation.progress.phase}
          pct={mutation.progress.pct}
        />
      )}

      {mutation.data && mutation.data.builds.length === 0 && (
        <div className="rounded-md border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
          {t("optimize.empty")}
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
          {t("optimize.hint").split("**").map((chunk, i) => (
            i % 2 === 1 ? <span key={i} className="font-semibold">{chunk}</span> : chunk
          ))}
        </div>
      )}
    </div>
  );
}
