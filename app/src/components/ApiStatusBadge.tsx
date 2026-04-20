import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

import { useHealth } from "@/api/hooks";
import { Badge } from "@/components/ui/badge";
import { getApiBaseUrl } from "@/lib/config";

export function ApiStatusBadge() {
  const query = useHealth();
  const baseUrl = getApiBaseUrl();

  if (query.isPending) {
    return (
      <Badge variant="secondary" className="gap-1.5">
        <Loader2 className="h-3 w-3 animate-spin" />
        Connecting to {baseUrl}
      </Badge>
    );
  }
  if (query.isError) {
    return (
      <Badge variant="destructive" className="gap-1.5">
        <AlertCircle className="h-3 w-3" />
        API offline ({baseUrl})
      </Badge>
    );
  }
  return (
    <Badge variant="success" className="gap-1.5">
      <CheckCircle2 className="h-3 w-3" />
      API v{query.data?.version} live
    </Badge>
  );
}
