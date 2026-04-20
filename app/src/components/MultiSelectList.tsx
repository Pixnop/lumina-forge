import { Check, Search } from "lucide-react";
import * as React from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { VaultItem } from "@/types/api";

interface Props {
  items: VaultItem[];
  value: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
  emptyMessage?: string;
  disabled?: (item: VaultItem) => boolean;
  renderMeta?: (item: VaultItem) => React.ReactNode;
}

export function MultiSelectList({
  items,
  value,
  onChange,
  placeholder = "Search…",
  emptyMessage = "Nothing to pick from yet.",
  disabled,
  renderMeta,
}: Props) {
  const [query, setQuery] = React.useState("");
  const selected = React.useMemo(() => new Set(value), [value]);

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (i) => i.name.toLowerCase().includes(q) || i.slug.includes(q),
    );
  }, [items, query]);

  function toggle(slug: string) {
    if (selected.has(slug)) {
      onChange(value.filter((s) => s !== slug));
    } else {
      onChange([...value, slug]);
    }
  }

  return (
    <div className="rounded-md border border-input bg-background">
      <div className="flex items-center gap-2 border-b border-input px-3 py-2">
        <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
        <Input
          className="h-8 border-none px-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="text-xs text-muted-foreground">
          {selected.size} selected
        </div>
      </div>
      <div className="max-h-64 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="px-3 py-6 text-center text-sm text-muted-foreground">
            {items.length === 0 ? emptyMessage : `No match for “${query}”`}
          </div>
        ) : (
          filtered.map((item) => {
            const isSelected = selected.has(item.slug);
            const isDisabled = disabled?.(item) ?? false;
            return (
              <button
                key={item.slug}
                type="button"
                disabled={isDisabled}
                onClick={() => toggle(item.slug)}
                className={cn(
                  "flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent",
                  isDisabled && "cursor-not-allowed opacity-50 hover:bg-transparent",
                )}
              >
                <span className="flex items-center gap-2">
                  <span
                    className={cn(
                      "flex h-4 w-4 items-center justify-center rounded border border-input",
                      isSelected && "bg-primary text-primary-foreground",
                    )}
                  >
                    {isSelected ? <Check className="h-3 w-3" /> : null}
                  </span>
                  <span>{item.name}</span>
                </span>
                {renderMeta ? (
                  <span className="text-xs text-muted-foreground">
                    {renderMeta(item)}
                  </span>
                ) : null}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
