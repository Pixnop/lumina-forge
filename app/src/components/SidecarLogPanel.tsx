import { invoke } from "@tauri-apps/api/core";
import { Eraser, Terminal } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SidecarLogPanel() {
  const [lines, setLines] = React.useState<string[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const scrollRef = React.useRef<HTMLPreElement>(null);

  React.useEffect(() => {
    let cancelled = false;

    async function refresh() {
      try {
        const next = await invoke<string[]>("get_sidecar_logs");
        if (cancelled) return;
        setLines(next);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        // `invoke` throws when not running inside Tauri (plain browser
        // dev mode) — surface a friendly note instead of a crash.
        setError((err as Error).message ?? String(err));
      }
    }

    refresh();
    const interval = window.setInterval(refresh, 1_000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  React.useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    // Auto-scroll only if already near bottom — don't yank the user back
    // mid-scroll.
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    if (nearBottom) el.scrollTop = el.scrollHeight;
  }, [lines]);

  async function clearLogs() {
    try {
      await invoke("clear_sidecar_logs");
      setLines([]);
    } catch {
      // ignore; refresh will pick up the real state anyway
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Terminal className="h-4 w-4 text-muted-foreground" />
          Sidecar log
        </CardTitle>
        <Button
          variant="ghost"
          size="sm"
          onClick={clearLogs}
          disabled={!!error || lines.length === 0}
        >
          <Eraser className="h-3.5 w-3.5" />
          Clear
        </Button>
      </CardHeader>
      <CardContent>
        {error ? (
          <p className="text-sm text-muted-foreground">
            Log pane available only inside the Tauri app — this is the Vite
            preview in a regular browser.
          </p>
        ) : lines.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No output yet. The Python API prints its own startup lines here —
            if the badge stays offline, whatever you see below is the reason.
          </p>
        ) : (
          <pre
            ref={scrollRef}
            className="max-h-72 overflow-y-auto rounded-md border border-border bg-secondary/40 p-3 text-xs leading-snug text-foreground/90"
          >
            {lines.join("\n")}
          </pre>
        )}
      </CardContent>
    </Card>
  );
}
