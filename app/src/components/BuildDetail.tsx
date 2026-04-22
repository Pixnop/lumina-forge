import { Award } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RankedBuildResponse } from "@/types/api";

interface Props {
  build: RankedBuildResponse;
}

export function BuildDetail({ build }: Props) {
  const { t } = useTranslation();
  const d = build.damage;
  const factors: [string, number][] = [
    [t("build.factor.base"), d.base],
    [t("build.factor.might"), d.might_mult],
    [t("build.factor.picto"), d.picto_mult],
    [t("build.factor.lumina"), d.lumina_mult],
    [t("build.factor.crit"), d.crit_mult],
    [t("build.factor.synergy"), d.synergy_mult],
    [t("build.factor.ap"), d.ap_mult],
  ];

  return (
    <div className="grid gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-2xl">
              {t("build.rank", { rank: build.rank })} — {build.loadout.weapon}
            </CardTitle>
            <div className="text-sm text-muted-foreground">
              {build.loadout.character}
            </div>
            {build.archetype && (
              <div className="mt-2 flex items-center gap-2">
                <Badge variant="success" className="gap-1">
                  <Award className="h-3.5 w-3.5" />
                  {build.archetype.name}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {build.archetype.dps_tier}-tier
                  {" · "}
                  {build.archetype.confidence === "variant"
                    ? t("build.archetype.variant")
                    : t("build.archetype.exact")}
                  {" · "}
                  {t("build.archetype.bonus", {
                    pct: (build.archetype.bonus_applied * 100).toFixed(0),
                  })}
                </span>
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              {t("build.total_score")}
            </div>
            <div className="text-3xl font-bold text-primary">
              {build.total_score.toFixed(0)}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2 text-sm">
            {factors.map(([label, value]) => (
              <div key={label} className="flex flex-col rounded-md border border-border bg-secondary/50 p-2">
                <span className="text-xs text-muted-foreground">{label}</span>
                <span className="font-semibold">
                  {label === "Base" ? value.toFixed(0) : `×${value.toFixed(2)}`}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-3 text-sm">
            {t("build.est_dps")} — <span className="font-bold">{d.est_dps.toFixed(0)}</span>
            {d.raw_dps > d.est_dps + 1 && (
              <span className="ml-2 text-xs text-muted-foreground">
                ({t("build.capped")} — {t("build.raw_dps")} {d.raw_dps.toFixed(0)})
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {build.weapon_alternatives.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{t("build.also_works")}</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border text-sm">
              {build.weapon_alternatives.map((alt, idx) => (
                <li
                  key={alt.weapon}
                  className="flex items-center justify-between py-2"
                >
                  <span className="flex items-center gap-2">
                    <Badge variant="outline" className="tabular-nums">
                      #{idx + 2}
                    </Badge>
                    <span className="font-medium">{alt.weapon}</span>
                  </span>
                  <span className="text-muted-foreground tabular-nums">
                    est. {alt.est_dps.toFixed(0)}
                    {alt.raw_dps > alt.est_dps + 1 && (
                      <span className="ml-2 text-xs">
                        (capped, raw {alt.raw_dps.toFixed(0)})
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t("build.loadout")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Row label={t("build.weapon")} items={[build.loadout.weapon]} />
          <Row label={t("build.pictos")} items={build.loadout.pictos} />
          <Row label={t("build.luminas")} items={build.loadout.luminas} />
          <Row label={t("build.skills")} items={build.loadout.skills_used} />
          {build.synergies_matched.length > 0 && (
            <Row label={t("build.synergies")} items={build.synergies_matched} variant="success" />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("build.rotation")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="list-decimal space-y-2 pl-5 text-sm">
            {build.rotation_hint.map((line) => (
              <li key={line} dangerouslySetInnerHTML={{ __html: formatBold(line) }} />
            ))}
          </ol>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("build.why")}</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {build.why.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {(build.utility.has_revive ||
        build.utility.has_heal ||
        build.utility.has_defense_buff) && (
        <Card>
          <CardHeader>
            <CardTitle>{t("build.utility")}</CardTitle>
          </CardHeader>
          <CardContent className="flex gap-2">
            {build.utility.has_revive && <Badge variant="success">Revive</Badge>}
            {build.utility.has_heal && <Badge variant="success">Heal</Badge>}
            {build.utility.has_defense_buff && (
              <Badge variant="success">Defense</Badge>
            )}
            <span className="ml-2 text-sm text-muted-foreground">
              score {build.utility.score_0_1.toFixed(2)}
            </span>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Row({
  label,
  items,
  variant,
}: {
  label: string;
  items: string[];
  variant?: "default" | "success";
}) {
  return (
    <div className="grid grid-cols-[96px_1fr] items-start gap-2 text-sm">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <div className="flex flex-wrap gap-1">
        {items.length === 0 ? (
          <span className="text-muted-foreground">—</span>
        ) : (
          items.map((slug) => (
            <Badge key={slug} variant={variant ?? "secondary"}>
              {slug}
            </Badge>
          ))
        )}
      </div>
    </div>
  );
}

function formatBold(text: string): string {
  // Naive **bold** → <strong>bold</strong>. Input is trusted (server-generated).
  return text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}
