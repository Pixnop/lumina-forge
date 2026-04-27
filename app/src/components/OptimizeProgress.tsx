import { Loader2 } from "lucide-react";
import * as React from "react";
import { useTranslation } from "react-i18next";

/**
 * Real progress bar driven by the sidecar's ``/optimize/stream``
 * NDJSON events. ``pct`` is the live ratio (0–1) and ``phase`` is one
 * of ``loading | scoring | ranking | done``. We render whichever is
 * larger between the live pct and a soft time-based floor — that way
 * the bar still creeps forward during the brief gaps between events
 * (vault load, ranking) and never feels stuck.
 */
export function OptimizeProgress({
  pictosCount,
  weaponsCount,
  phase,
  pct,
}: {
  pictosCount: number;
  weaponsCount: number;
  phase: string;
  pct: number;
}) {
  const { t } = useTranslation();
  const expectedSeconds = estimateSeconds(pictosCount, weaponsCount);
  const [floor, setFloor] = React.useState(2);
  const [elapsed, setElapsed] = React.useState(0);

  React.useEffect(() => {
    const startedAt = performance.now();
    const id = window.setInterval(() => {
      const ms = performance.now() - startedAt;
      const ratio = Math.min(0.9, ms / 1000 / expectedSeconds);
      setFloor(2 + ratio * 88);
      setElapsed(ms / 1000);
    }, 100);
    return () => window.clearInterval(id);
  }, [expectedSeconds]);

  const livePct = Math.max(2, pct * 100);
  const finalPct = Math.max(livePct, floor);
  const phaseLabel = t(`optimize.phase.${phase}`, { defaultValue: phase });

  return (
    <div className="space-y-3 rounded-md border border-dashed border-border py-8 px-4">
      <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        {t("optimize.loading")} · {phaseLabel}
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary/40">
        <div
          className="h-full rounded-full bg-primary transition-[width] duration-150 ease-linear"
          style={{ width: `${finalPct.toFixed(1)}%` }}
        />
      </div>
      <div className="flex justify-between text-xs tabular-nums text-muted-foreground">
        <span>{t("optimize.elapsed", { seconds: elapsed.toFixed(1) })}</span>
        <span>
          {finalPct.toFixed(0)} % · {pictosCount} pictos · {weaponsCount}{" "}
          {t("optimize.weapons_word")}
        </span>
      </div>
    </div>
  );
}

/**
 * Soft time-based floor used when the stream is between events. Tuned
 * against the optimized sidecar (~17 s on a 134-pictos × 18-weapons
 * inventory). The bar never relies on this alone — the live pct from
 * the stream wins as soon as it overtakes the floor.
 */
function estimateSeconds(pictosCount: number, weaponsCount: number): number {
  const w = Math.max(weaponsCount, 1);
  const p = Math.max(pictosCount, 3);
  const combos = Math.min(w * choose3(p), 100_000);
  return Math.max(2, Math.round(2 + combos * 0.00015));
}

function choose3(n: number): number {
  if (n < 3) return 0;
  return (n * (n - 1) * (n - 2)) / 6;
}
