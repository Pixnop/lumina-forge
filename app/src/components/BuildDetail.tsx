import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RankedBuildResponse } from "@/types/api";

interface Props {
  build: RankedBuildResponse;
}

export function BuildDetail({ build }: Props) {
  const d = build.damage;
  const factors: [string, number][] = [
    ["Base", d.base],
    ["× Might", d.might_mult],
    ["× Picto", d.picto_mult],
    ["× Lumina", d.lumina_mult],
    ["× Crit", d.crit_mult],
    ["× Synergy", d.synergy_mult],
  ];

  return (
    <div className="grid gap-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-2xl">
              #{build.rank} — {build.loadout.weapon}
            </CardTitle>
            <div className="text-sm text-muted-foreground">
              {build.loadout.character}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              Total score
            </div>
            <div className="text-3xl font-bold text-primary">
              {build.total_score.toFixed(0)}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-6 gap-2 text-sm">
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
            est. DPS — <span className="font-bold">{d.est_dps.toFixed(0)}</span>
            {d.raw_dps > d.est_dps + 1 && (
              <span className="ml-2 text-xs text-muted-foreground">
                (capped — raw {d.raw_dps.toFixed(0)})
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {build.weapon_alternatives.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Also works with</CardTitle>
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
          <CardTitle>Loadout</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Row label="Weapon" items={[build.loadout.weapon]} />
          <Row label="Pictos" items={build.loadout.pictos} />
          <Row label="Luminas" items={build.loadout.luminas} />
          <Row label="Skills" items={build.loadout.skills_used} />
          {build.synergies_matched.length > 0 && (
            <Row label="Synergies" items={build.synergies_matched} variant="success" />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Rotation</CardTitle>
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
          <CardTitle>Why this build</CardTitle>
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
            <CardTitle>Utility</CardTitle>
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
