import { Target } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AspirationalBuild } from "@/types/api";

interface Props {
  aspirational: AspirationalBuild[];
}

export function AspirationalList({ aspirational }: Props) {
  if (aspirational.length === 0) return null;
  return (
    <Card className="border-amber-500/40 bg-amber-500/5">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <Target className="h-4 w-4 text-amber-500" />
          Close to: curated archetypes you can almost run
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {aspirational.map((entry) => (
          <div
            key={entry.slug}
            className="rounded-md border border-border bg-card/50 p-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-semibold">{entry.name}</span>
                {entry.dps_tier && (
                  <Badge variant="outline" className="text-xs">
                    {entry.dps_tier}-tier
                  </Badge>
                )}
              </div>
            </div>
            <div className="mt-2 flex flex-wrap gap-1 text-xs text-muted-foreground">
              <span>Missing:</span>
              {entry.missing_weapon && (
                <Badge variant="outline">weapon · {entry.missing_weapon}</Badge>
              )}
              {entry.missing_pictos.map((slug) => (
                <Badge key={`p-${slug}`} variant="outline">
                  picto · {slug}
                </Badge>
              ))}
              {entry.missing_luminas.map((slug) => (
                <Badge key={`lu-${slug}`} variant="outline">
                  lumina · {slug}
                </Badge>
              ))}
              {entry.missing_skills.map((slug) => (
                <Badge key={`s-${slug}`} variant="outline">
                  skill · {slug}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
