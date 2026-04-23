import type { TFunction } from "i18next";
import { Copy, Save, Trash2, Upload } from "lucide-react";
import * as React from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useInventoryStore } from "@/stores/inventory";
import { useLibraryStore } from "@/stores/library";

export function InventoryLibrary() {
  const { t } = useTranslation();
  const draft = useInventoryStore((s) => s.draft);
  const setDraft = useInventoryStore((s) => s.setDraft);
  const items = useLibraryStore((s) => s.items);
  const save = useLibraryStore((s) => s.save);
  const remove = useLibraryStore((s) => s.remove);
  const duplicate = useLibraryStore((s) => s.duplicate);

  const [name, setName] = React.useState("");

  function saveCurrent() {
    const trimmed = name.trim() || `${draft.character} loadout`;
    save(trimmed, draft);
    setName("");
  }

  const relativeTime = React.useCallback((ts: number) => _relativeTime(ts, t), [t]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{t("library.title")}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t("library.placeholder", { character: draft.character })}
            onKeyDown={(e) => {
              if (e.key === "Enter") saveCurrent();
            }}
          />
          <Button variant="outline" onClick={saveCurrent}>
            <Save className="h-4 w-4" />
            {t("library.save_current")}
          </Button>
        </div>

        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("library.empty")}</p>
        ) : (
          <ul className="divide-y divide-border rounded-md border border-input">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between gap-3 px-3 py-2 text-sm"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium">{item.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {item.character} — {t("library.saved_suffix", { ago: relativeTime(item.updatedAt) })}
                  </div>
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDraft(item.inventory)}
                    title={t("library.load_tooltip")}
                  >
                    <Upload className="h-3.5 w-3.5" />
                    {t("library.load")}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => duplicate(item.id)}
                    title={t("library.duplicate_tooltip")}
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => remove(item.id)}
                    title={t("library.delete_tooltip")}
                    className="text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function _relativeTime(ts: number, t: TFunction): string {
  const seconds = Math.round((Date.now() - ts) / 1000);
  if (seconds < 60) return t("library.time.just_now");
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return t("library.time.minutes_ago", { count: minutes });
  const hours = Math.round(minutes / 60);
  if (hours < 24) return t("library.time.hours_ago", { count: hours });
  const days = Math.round(hours / 24);
  if (days < 30) return t("library.time.days_ago", { count: days });
  return new Date(ts).toLocaleDateString();
}
