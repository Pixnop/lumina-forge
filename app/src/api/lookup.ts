import * as React from "react";

import { useVaultItems } from "@/api/hooks";
import { getApiBaseUrl } from "@/lib/config";
import type { VaultItem, VaultItemType } from "@/types/api";

export interface ResolvedItem {
  slug: string;
  name: string;
  type: VaultItemType;
  imageUrl: string | null;
  raw: VaultItem;
}

/**
 * Build a slug → ResolvedItem lookup across every vault type. Lets the
 * build views replace opaque slugs with a name + thumbnail without
 * threading per-slug fetches through every call site. All queries share
 * TanStack Query's cache, so this composes freely with the Vault browser.
 */
export function useItemLookup(): (slug: string) => ResolvedItem | undefined {
  const pictos = useVaultItems("picto");
  const luminas = useVaultItems("lumina");
  const weapons = useVaultItems("weapon");
  const skills = useVaultItems("skill");
  const chars = useVaultItems("character");

  const baseUrl = getApiBaseUrl();

  const index = React.useMemo(() => {
    const map = new Map<string, ResolvedItem>();
    const sources: [VaultItemType, VaultItem[] | undefined][] = [
      ["weapon", weapons.data?.items],
      ["picto", pictos.data?.items],
      ["lumina", luminas.data?.items],
      ["skill", skills.data?.items],
      ["character", chars.data?.items],
    ];
    for (const [type, items] of sources) {
      if (!items) continue;
      for (const item of items) {
        if (map.has(item.slug)) continue; // first source wins
        map.set(item.slug, {
          slug: item.slug,
          name: item.name,
          type,
          imageUrl: item.image_path ? `${baseUrl}/assets/${item.image_path}` : null,
          raw: item,
        });
      }
    }
    return map;
  }, [
    baseUrl,
    pictos.data,
    luminas.data,
    weapons.data,
    skills.data,
    chars.data,
  ]);

  return React.useCallback((slug: string) => index.get(slug), [index]);
}
