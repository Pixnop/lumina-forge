import { Link, useParams } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

import { BuildDetail } from "@/components/BuildDetail";
import { useTeamStore } from "@/stores/team";

export function TeamBuildDetailPage() {
  const { rank, slot } = useParams({ from: "/team/$rank/$slot" });
  const found = useTeamStore((s) => s.findMember(Number(rank), Number(slot)));

  if (!found) {
    return (
      <div className="space-y-4 text-center">
        <h2 className="text-2xl font-semibold">Build not found</h2>
        <p className="text-sm text-muted-foreground">
          Re-run the team optimizer first.
        </p>
        <Link
          to="/team"
          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to team
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Link
        to="/team"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to team
      </Link>
      <div className="text-sm text-muted-foreground">
        Team #{rank} · <span className="font-medium capitalize">{found.characterSlug}</span>
      </div>
      <BuildDetail build={found.build} />
    </div>
  );
}
