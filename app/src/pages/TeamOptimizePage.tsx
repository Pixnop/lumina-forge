import { Link, useNavigate } from "@tanstack/react-router";
import { AlertCircle, ArrowLeft, Loader2, Users, Wand2, X } from "lucide-react";
import * as React from "react";
import { useTranslation } from "react-i18next";

import { useOptimizeTeam } from "@/api/hooks";
import { BuildCard } from "@/components/BuildCard";
import { OptimizeProgress } from "@/components/OptimizeProgress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTeamStore } from "@/stores/team";
import type { Inventory, Mode, TeamBuildResponse } from "@/types/api";

export function TeamOptimizePage() {
  const { t } = useTranslation();
  const members = useTeamStore((s) => s.members);
  const removeMember = useTeamStore((s) => s.removeMember);
  const setResults = useTeamStore((s) => s.setResults);
  const results = useTeamStore((s) => s.results);
  const mutation = useOptimizeTeam();
  const [mode, setMode] = React.useState<Mode>("dps");
  const [top, setTop] = React.useState(5);

  const totalPictos = React.useMemo(() => {
    const all = new Set<string>();
    for (const m of members) for (const p of m.pictos_available) all.add(p);
    return all.size;
  }, [members]);
  const totalWeapons = React.useMemo(
    () => members.reduce((acc, m) => acc + m.weapons_available.length, 0),
    [members],
  );

  function run() {
    mutation.mutate(
      { inventories: members, mode, top },
      { onSuccess: (data) => setResults(data) },
    );
  }

  if (members.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">{t("team.title")}</h1>
        <Card className="border-dashed">
          <CardContent className="space-y-3 py-8 text-center text-sm text-muted-foreground">
            <Users className="mx-auto h-8 w-8 text-muted-foreground/60" />
            <p>{t("team.empty_hint")}</p>
            <Link to="/" className="inline-flex items-center gap-1 text-primary hover:underline">
              <ArrowLeft className="h-3.5 w-3.5" />
              {t("team.go_to_import")}
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const teams = mutation.data?.teams ?? results?.teams ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Link to="/" className="inline-flex items-center gap-1 hover:text-foreground">
              <ArrowLeft className="h-3.5 w-3.5" />
              {t("team.back")}
            </Link>
          </div>
          <h1 className="mt-1 flex items-center gap-2 text-3xl font-bold tracking-tight">
            <Users className="h-7 w-7 text-primary" />
            {t("team.title")}
          </h1>
          <p className="text-sm text-muted-foreground">
            {t("team.summary", {
              members: members.length,
              pictos: totalPictos,
              weapons: totalWeapons,
            })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={mode} onValueChange={(v) => setMode(v as Mode)}>
            <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="dps">{t("optimize.mode.dps")}</SelectItem>
              <SelectItem value="balanced">{t("optimize.mode.balanced")}</SelectItem>
              <SelectItem value="utility">{t("optimize.mode.utility")}</SelectItem>
            </SelectContent>
          </Select>
          <Select value={String(top)} onValueChange={(v) => setTop(Number(v))}>
            <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
            <SelectContent>
              {[3, 5, 10].map((n) => (
                <SelectItem key={n} value={String(n)}>
                  {t("optimize.top", { count: n })}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={run} disabled={mutation.isPending || members.length < 2}>
            {mutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Wand2 className="h-4 w-4" />
            )}
            {t("team.run")}
          </Button>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-3">
        {members.map((m, i) => (
          <Card key={`${m.character}-${i}`} className="border-primary/30 bg-primary/5">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="flex items-center gap-2 text-base capitalize">
                <Badge variant="outline" className="text-xs">{i + 1}</Badge>
                {m.character}
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeMember(i)}
                disabled={mutation.isPending}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-1 text-xs text-muted-foreground">
              <span>{t("team.member.level", { lvl: m.level })}</span>
              <span>{t("team.member.pp", { pp: m.pp_budget })}</span>
              <span>{t("team.member.weapons", { n: m.weapons_available.length })}</span>
              <span>{t("team.member.pictos", { n: m.pictos_available.length })}</span>
            </CardContent>
          </Card>
        ))}
      </div>

      {mutation.isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive bg-destructive/10 px-3 py-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          {(mutation.error as Error).message}
        </div>
      )}

      {mutation.isPending && (
        <OptimizeProgress
          pictosCount={totalPictos}
          weaponsCount={totalWeapons}
          phase={mutation.progress.phase}
          pct={mutation.progress.pct}
        />
      )}

      {teams.length === 0 && !mutation.isPending && (
        <div className="rounded-md border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
          {t("team.run_hint")}
        </div>
      )}

      {teams.map((team, idx) => (
        <TeamSlot key={idx} rank={idx + 1} team={team} members={members} />
      ))}
    </div>
  );
}

function TeamSlot({
  rank,
  team,
  members,
}: {
  rank: number;
  team: TeamBuildResponse;
  members: Inventory[];
}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Badge className="text-base">#{rank}</Badge>
            {t("team.composition_title")}
          </CardTitle>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              {t("team.total_score")}
            </div>
            <div className="text-2xl font-bold text-primary">
              {team.total_score.toFixed(0)}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 lg:grid-cols-3">
          {team.members.map((m, slot) => (
            <div key={m.inventory_index} className="space-y-1">
              <div className="text-xs uppercase tracking-wide text-muted-foreground">
                {members[m.inventory_index]?.character ?? `#${m.inventory_index}`}
              </div>
              <BuildCard
                rank={m.build.rank}
                build={m.build}
                onClick={() =>
                  navigate({
                    to: "/team/$rank/$slot",
                    params: { rank: String(rank), slot: String(slot) },
                  })
                }
              />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
