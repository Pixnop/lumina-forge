import { Copy, Save, Trash2, Upload } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useInventoryStore } from "@/stores/inventory";
import { useLibraryStore } from "@/stores/library";

export function InventoryLibrary() {
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

  const relativeTime = React.useCallback(_relativeTime, []);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Saved inventories</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={`e.g. "${draft.character} — glass cannon"`}
            onKeyDown={(e) => {
              if (e.key === "Enter") saveCurrent();
            }}
          />
          <Button variant="outline" onClick={saveCurrent}>
            <Save className="h-4 w-4" />
            Save current
          </Button>
        </div>

        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No saved loadouts yet. Saving stashes the current inventory as a
            named copy you can load later.
          </p>
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
                    {item.character} — saved {relativeTime(item.updatedAt)}
                  </div>
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDraft(item.inventory)}
                    title="Replace current draft with this saved inventory"
                  >
                    <Upload className="h-3.5 w-3.5" />
                    Load
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => duplicate(item.id)}
                    title="Duplicate this entry"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => remove(item.id)}
                    title="Delete this entry"
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

function _relativeTime(ts: number): string {
  const seconds = Math.round((Date.now() - ts) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days} d ago`;
  return new Date(ts).toLocaleDateString();
}
