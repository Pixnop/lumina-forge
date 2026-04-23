import { RefreshCw, Save } from "lucide-react";
import * as React from "react";
import { useTranslation } from "react-i18next";

import { useVaultInfo, useVaultReload } from "@/api/hooks";
import { ApiStatusBadge } from "@/components/ApiStatusBadge";
import { SidecarLogPanel } from "@/components/SidecarLogPanel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AVAILABLE_LOCALES,
  getStoredLocale,
  type Locale,
  setStoredLocale,
} from "@/i18n";
import {
  DEFAULT_API_BASE_URL,
  getApiBaseUrl,
  resetApiBaseUrl,
  setApiBaseUrl,
} from "@/lib/config";

export function SettingsPage() {
  const { t } = useTranslation();
  const [url, setUrl] = React.useState(getApiBaseUrl());
  const [locale, setLocale] = React.useState<Locale>(getStoredLocale());
  const info = useVaultInfo();
  const reload = useVaultReload();

  function save() {
    setApiBaseUrl(url);
    window.location.reload();
  }

  function reset() {
    resetApiBaseUrl();
    setUrl(DEFAULT_API_BASE_URL);
  }

  function changeLocale(next: Locale) {
    setLocale(next);
    setStoredLocale(next);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{t("settings.title")}</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("settings.language")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Select value={locale} onValueChange={(v) => changeLocale(v as Locale)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AVAILABLE_LOCALES.map((l) => (
                <SelectItem key={l} value={l}>
                  {l === "fr" ? "Français" : "English"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>{t("settings.api_url")}</CardTitle>
          <ApiStatusBadge />
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="api-url">{t("settings.api_url")}</Label>
            <Input
              id="api-url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="http://127.0.0.1:31733"
            />
            <p className="text-xs text-muted-foreground">
              {t("settings.api_url_hint", { url: DEFAULT_API_BASE_URL })}
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={save}>
              <Save className="h-4 w-4" />
              {t("settings.save")}
            </Button>
            <Button variant="outline" onClick={reset}>
              {t("settings.reset")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>{t("settings.vault_snapshot")}</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => reload.mutate()}
            disabled={reload.isPending}
          >
            <RefreshCw
              className={`h-4 w-4 ${reload.isPending ? "animate-spin" : ""}`}
            />
            {t("settings.reload_vault")}
          </Button>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-3 text-sm">
          {info.data ? (
            Object.entries(info.data).map(([key, value]) => (
              <div key={key} className="rounded-md border border-border p-3">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  {t(`settings.kind.${key}`, key)}
                </div>
                <div className="text-2xl font-bold">{value}</div>
              </div>
            ))
          ) : (
            <div className="col-span-3 text-sm text-muted-foreground">
              {info.isPending ? t("settings.vault_loading") : t("settings.vault_offline")}
            </div>
          )}
        </CardContent>
      </Card>

      <SidecarLogPanel />
    </div>
  );
}
