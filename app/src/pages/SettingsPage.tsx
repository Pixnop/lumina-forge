import { RefreshCw, Save } from "lucide-react";
import * as React from "react";

import { useVaultInfo, useVaultReload } from "@/api/hooks";
import { ApiStatusBadge } from "@/components/ApiStatusBadge";
import { SidecarLogPanel } from "@/components/SidecarLogPanel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  DEFAULT_API_BASE_URL,
  getApiBaseUrl,
  resetApiBaseUrl,
  setApiBaseUrl,
} from "@/lib/config";

export function SettingsPage() {
  const [url, setUrl] = React.useState(getApiBaseUrl());
  const info = useVaultInfo();
  const reload = useVaultReload();

  function save() {
    setApiBaseUrl(url);
    // Force reload so TanStack Query swaps its base URL.
    window.location.reload();
  }

  function reset() {
    resetApiBaseUrl();
    setUrl(DEFAULT_API_BASE_URL);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Point the app at a different API and inspect what the vault currently
          holds.
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>API endpoint</CardTitle>
          <ApiStatusBadge />
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="api-url">Base URL</Label>
            <Input
              id="api-url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="http://127.0.0.1:8000"
            />
            <p className="text-xs text-muted-foreground">
              Default: {DEFAULT_API_BASE_URL}. The app will reload to apply.
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={save}>
              <Save className="h-4 w-4" />
              Save & reload
            </Button>
            <Button variant="outline" onClick={reset}>
              Reset to default
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Vault snapshot</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => reload.mutate()}
            disabled={reload.isPending}
          >
            <RefreshCw
              className={`h-4 w-4 ${reload.isPending ? "animate-spin" : ""}`}
            />
            Reload vault
          </Button>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-3 text-sm">
          {info.data ? (
            Object.entries(info.data).map(([key, value]) => (
              <div key={key} className="rounded-md border border-border p-3">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  {key}
                </div>
                <div className="text-2xl font-bold">{value}</div>
              </div>
            ))
          ) : (
            <div className="col-span-3 text-sm text-muted-foreground">
              {info.isPending ? "loading…" : "vault offline"}
            </div>
          )}
        </CardContent>
      </Card>

      <SidecarLogPanel />
    </div>
  );
}
