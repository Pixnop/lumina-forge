import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/client";
import type { OptimizeRequest, VaultItemType } from "@/types/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 10_000,
    retry: 1,
  });
}

export function useVaultInfo() {
  return useQuery({
    queryKey: ["vault", "info"],
    queryFn: api.vaultInfo,
    staleTime: 30_000,
  });
}

export function useVaultItems(type: VaultItemType, character?: string) {
  return useQuery({
    queryKey: ["vault", "items", type, character ?? null],
    queryFn: () => api.vaultItems(type, character),
    staleTime: 60_000,
  });
}

export function useOptimize() {
  return useMutation({
    mutationFn: (body: OptimizeRequest) => api.optimize(body),
  });
}

export function useVaultReload() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.vaultReload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vault"] });
    },
  });
}
