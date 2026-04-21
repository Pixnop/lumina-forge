import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import * as React from "react";

import { useHealth } from "@/api/hooks";
import { Badge } from "@/components/ui/badge";
import { getApiBaseUrl } from "@/lib/config";

// The sidecar typically boots in 3-5 s on Windows. Show "Connecting…"
// for this window even when the first fetches fail — "API offline" is
// misleading while the user is still watching the splash.
const STARTUP_GRACE_MS = 15_000;

export function ApiStatusBadge() {
  const query = useHealth();
  const baseUrl = getApiBaseUrl();
  const [mountedAt] = React.useState(() => Date.now());
  const [now, setNow] = React.useState(() => Date.now());

  React.useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 1_000);
    return () => window.clearInterval(interval);
  }, []);

  const inGrace = now - mountedAt < STARTUP_GRACE_MS;

  if (query.isSuccess) {
    return (
      <Badge variant="success" className="gap-1.5">
        <CheckCircle2 className="h-3 w-3" />
        API v{query.data?.version} live
      </Badge>
    );
  }

  if (inGrace || query.isPending) {
    return (
      <Badge variant="secondary" className="gap-1.5">
        <Loader2 className="h-3 w-3 animate-spin" />
        Connecting…
      </Badge>
    );
  }

  return (
    <Badge variant="destructive" className="gap-1.5">
      <AlertCircle className="h-3 w-3" />
      API offline ({baseUrl})
    </Badge>
  );
}
