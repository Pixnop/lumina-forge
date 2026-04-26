import { Award, ChevronRight, Sparkles, Sword } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RankedBuildResponse } from "@/types/api";

interface Props {
  rank: number;
  build: RankedBuildResponse;
  active?: boolean;
  onClick?: () => void;
}

export function BuildCard({ rank, build, active, onClick }: Props) {
  return (
    <Card
      onClick={onClick}
      className={`cursor-pointer transition hover:border-primary ${
        active ? "border-primary ring-1 ring-primary" : ""
      }`}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Badge variant="outline" className="text-base">
              #{rank}
            </Badge>
            <Sword className="h-4 w-4 text-muted-foreground" />
            {build.loadout.weapon}
          </CardTitle>
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        </div>
        {build.archetype && (
          <div className="mt-1 flex items-center gap-2">
            <Badge variant="success" className="gap-1">
              <Award className="h-3 w-3" />
              {build.archetype.name}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {build.archetype.dps_tier}-tier
              {build.archetype.confidence === "variant" && " · variant"}
            </span>
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <Stat
            label={
              build.damage.raw_dps > build.damage.est_dps + 1
                ? "DPS (capped)"
                : "DPS"
            }
            value={build.damage.est_dps.toFixed(0)}
          />
          <Stat
            label="Raw"
            value={build.damage.raw_dps.toFixed(0)}
            emphasis={build.damage.raw_dps > build.damage.est_dps + 1}
          />
          <Stat label="Picto mult" value={`×${build.damage.picto_mult.toFixed(2)}`} />
          <Stat label="Lumina mult" value={`×${build.damage.lumina_mult.toFixed(2)}`} />
        </div>

        <div className="flex flex-wrap gap-1">
          {build.loadout.pictos.map((slug) => (
            <Badge key={slug} variant="secondary" className="gap-1">
              <Sparkles className="h-3 w-3" />
              {slug}
            </Badge>
          ))}
        </div>

        {build.loadout.luminas.length > 0 && (
          <div className="text-xs text-muted-foreground">
            Luminas: {build.loadout.luminas.join(", ")}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Stat({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div className="flex flex-col">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className={emphasis ? "text-lg font-bold text-primary" : "font-medium"}>
        {value}
      </span>
    </div>
  );
}
