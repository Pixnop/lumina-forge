import { Search } from "lucide-react";
import * as React from "react";

import { useVaultItems } from "@/api/hooks";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { VaultItem, VaultItemType } from "@/types/api";

type TypeOption = { value: VaultItemType; label: string };

const TYPE_OPTIONS: TypeOption[] = [
  { value: "picto", label: "Pictos" },
  { value: "lumina", label: "Luminas" },
  { value: "weapon", label: "Weapons" },
  { value: "skill", label: "Skills" },
  { value: "character", label: "Characters" },
];

export function VaultPage() {
  const [type, setType] = React.useState<VaultItemType>("picto");
  const [query, setQuery] = React.useState("");
  const { data, isLoading, isError, error } = useVaultItems(type);

  const items = React.useMemo(() => {
    const list = data?.items ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter(
      (it) =>
        it.name.toLowerCase().includes(q) ||
        it.slug.toLowerCase().includes(q) ||
        (it.effect ?? "").toLowerCase().includes(q),
    );
  }, [data, query]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Vault browser</h1>
        <p className="text-sm text-muted-foreground">
          Every picto, lumina, weapon, skill and character the scraper has
          loaded — with all their parsed structured data.
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-1">
          {TYPE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setType(opt.value)}
              className={`rounded-md border px-3 py-1.5 text-sm transition ${
                type === opt.value
                  ? "border-primary bg-primary/10 font-semibold text-foreground"
                  : "border-border text-muted-foreground hover:text-foreground"
              }`}
            >
              {opt.label}
              {data && type === opt.value && (
                <span className="ml-1.5 text-xs text-muted-foreground">
                  {items.length}/{data.items.length}
                </span>
              )}
            </button>
          ))}
        </div>
        <div className="relative max-w-xs sm:w-64">
          <Search className="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by name, slug or effect…"
            className="pl-8"
          />
        </div>
      </div>

      {isLoading && (
        <div className="rounded-md border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
          Loading…
        </div>
      )}

      {isError && (
        <div className="rounded-md border border-destructive bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {(error as Error).message}
        </div>
      )}

      {!isLoading && items.length === 0 && (
        <div className="rounded-md border border-dashed border-border py-12 text-center text-sm text-muted-foreground">
          {data?.items.length === 0 ? "Vault is empty." : "No results for this query."}
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <VaultItemCard key={item.slug} item={item} type={type} />
        ))}
      </div>
    </div>
  );
}

function VaultItemCard({ item, type }: { item: VaultItem; type: VaultItemType }) {
  return (
    <Card>
      <CardContent className="space-y-2 py-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="font-semibold">{item.name}</div>
            <div className="text-xs text-muted-foreground">{item.slug}</div>
          </div>
          <div className="flex flex-wrap justify-end gap-1">
            {item.category && (
              <Badge variant="outline" className="text-xs">
                {item.category}
              </Badge>
            )}
            {item.character && (
              <Badge variant="outline" className="text-xs">
                {item.character}
              </Badge>
            )}
            {item.pp_cost != null && (
              <Badge variant="outline" className="text-xs">
                PP {item.pp_cost}
              </Badge>
            )}
            {item.ap_cost != null && (
              <Badge variant="outline" className="text-xs">
                AP {item.ap_cost}
              </Badge>
            )}
            {item.base_damage != null && (
              <Badge variant="outline" className="text-xs">
                ⚔ {item.base_damage}
              </Badge>
            )}
            {item.scaling_stat && (
              <Badge variant="outline" className="text-xs">
                {item.scaling_stat}
              </Badge>
            )}
          </div>
        </div>

        {item.effect && (
          <p className="text-sm text-muted-foreground">{item.effect}</p>
        )}

        <StructuredChips data={item.effect_structured} />

        {item.stats_granted && Object.keys(item.stats_granted).length > 0 && (
          <div className="flex flex-wrap gap-1">
            {Object.entries(item.stats_granted).map(([stat, value]) => (
              <Badge key={stat} variant="secondary" className="text-xs">
                {stat} +{value}
              </Badge>
            ))}
          </div>
        )}

        {type === "weapon" && item.passives && item.passives.length > 0 && (
          <WeaponPassives passives={item.passives} />
        )}
      </CardContent>
    </Card>
  );
}

function StructuredChips({ data }: { data: VaultItem["effect_structured"] }) {
  if (!data || Object.keys(data).length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1">
      {Object.entries(data).map(([key, value]) => (
        <Badge
          key={key}
          variant={isDamageField(key) ? "success" : "secondary"}
          className="text-xs tabular-nums"
        >
          {formatField(key, value)}
        </Badge>
      ))}
    </div>
  );
}

function WeaponPassives({
  passives,
}: {
  passives: Array<Record<string, unknown>>;
}) {
  return (
    <div className="space-y-1 border-t border-border pt-2 text-xs">
      {passives.map((p, idx) => {
        const name = typeof p.name === "string" ? p.name : `Passive ${idx + 1}`;
        const effect = typeof p.effect === "string" ? p.effect : "";
        const structured =
          p.effect_structured && typeof p.effect_structured === "object"
            ? (p.effect_structured as Record<string, unknown>)
            : undefined;
        return (
          <div key={`${name}-${idx}`}>
            <span className="font-semibold">{name}</span>
            {effect && <span className="ml-1 text-muted-foreground">{effect}</span>}
            {structured && Object.keys(structured).length > 0 && (
              <div className="mt-0.5 flex flex-wrap gap-1">
                {Object.entries(structured).map(([k, v]) => (
                  <Badge key={k} variant="outline" className="text-[10px] tabular-nums">
                    {formatField(k, v)}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function isDamageField(key: string) {
  return (
    key.includes("damage") ||
    key.includes("crit") ||
    key === "trigger_uptime"
  );
}

function formatField(key: string, value: unknown): string {
  if (typeof value === "boolean") return `${key}: ${value ? "yes" : "no"}`;
  if (typeof value === "number") {
    if (key.endsWith("_bonus") || key.endsWith("_mult") || key === "trigger_uptime") {
      return `${key}: ${(value * 100).toFixed(0)}%`;
    }
    return `${key}: ${value}`;
  }
  if (Array.isArray(value)) return `${key}: [${value.join(", ")}]`;
  if (typeof value === "string") return `${key}: ${value}`;
  return `${key}: ${JSON.stringify(value)}`;
}
