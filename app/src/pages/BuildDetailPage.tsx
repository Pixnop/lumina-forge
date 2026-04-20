import { Link, useParams } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";

import { BuildDetail } from "@/components/BuildDetail";
import { useResultsStore } from "@/stores/results";

export function BuildDetailPage() {
  const { rank } = useParams({ from: "/builds/$rank" });
  const build = useResultsStore((s) => s.findByRank(Number(rank)));

  if (!build) {
    return (
      <div className="space-y-4 text-center">
        <h2 className="text-2xl font-semibold">Build not found</h2>
        <p className="text-sm text-muted-foreground">
          Run the optimizer first from the Optimize page.
        </p>
        <Link
          to="/optimize"
          className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Go to Optimize
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Link
        to="/optimize"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to ranking
      </Link>
      <BuildDetail build={build} />
    </div>
  );
}
