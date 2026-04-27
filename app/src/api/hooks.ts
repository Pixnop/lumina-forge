import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as React from "react";

import { ApiError, api } from "@/api/client";
import type {
  OptimizeRequest,
  OptimizeResponse,
  TeamOptimizeRequest,
  TeamOptimizeResponse,
  VaultItemType,
} from "@/types/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    // Poll fast on failure so the badge recovers as soon as the
    // sidecar finishes booting (usually 3-5 s on Windows). Back off to
    // 10 s once we're connected to avoid hammering /health.
    refetchInterval: (query) => (query.state.error ? 2_000 : 10_000),
    refetchIntervalInBackground: true,
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

/**
 * Drives the streaming /optimize/stream endpoint. Exposes the same
 * shape the rest of the app expects from a mutation (``mutate``,
 * ``isPending``, ``error``, ``data``) plus a live ``progress`` state
 * the OptimizeProgress component reads to fill the bar in real time.
 */
export function useOptimize() {
  const [data, setData] = React.useState<OptimizeResponse | undefined>(undefined);
  const [error, setError] = React.useState<Error | null>(null);
  const [isPending, setPending] = React.useState(false);
  const [progress, setProgress] = React.useState<{ phase: string; pct: number }>({
    phase: "loading",
    pct: 0,
  });

  const mutate = React.useCallback(
    (
      body: OptimizeRequest,
      callbacks?: { onSuccess?: (d: OptimizeResponse) => void },
    ) => {
      setPending(true);
      setError(null);
      setData(undefined);
      setProgress({ phase: "loading", pct: 0 });

      (async () => {
        try {
          for await (const event of api.optimizeStream(body)) {
            if (event.event === "progress") {
              setProgress({ phase: event.phase, pct: event.pct });
            } else if (event.event === "result") {
              setData(event.data);
              setProgress({ phase: "done", pct: 1 });
              callbacks?.onSuccess?.(event.data);
            } else if (event.event === "error") {
              throw new ApiError(500, event.detail);
            }
          }
        } catch (e) {
          setError(e as Error);
        } finally {
          setPending(false);
        }
      })();
    },
    [],
  );

  return {
    mutate,
    data,
    error,
    isPending,
    isError: error !== null,
    progress,
  };
}

/** Streaming counterpart of {@link useOptimize} for 2- or 3-character parties. */
export function useOptimizeTeam() {
  const [data, setData] = React.useState<TeamOptimizeResponse | undefined>(undefined);
  const [error, setError] = React.useState<Error | null>(null);
  const [isPending, setPending] = React.useState(false);
  const [progress, setProgress] = React.useState<{ phase: string; pct: number }>({
    phase: "loading",
    pct: 0,
  });

  const mutate = React.useCallback(
    (
      body: TeamOptimizeRequest,
      callbacks?: { onSuccess?: (d: TeamOptimizeResponse) => void },
    ) => {
      setPending(true);
      setError(null);
      setData(undefined);
      setProgress({ phase: "preparing", pct: 0 });

      (async () => {
        let gotResult = false;
        try {
          for await (const event of api.optimizeTeamStream(body)) {
            if (event.event === "progress") {
              setProgress({ phase: event.phase, pct: event.pct });
            } else if (event.event === "result") {
              gotResult = true;
              setData(event.data);
              setProgress({ phase: "done", pct: 1 });
              callbacks?.onSuccess?.(event.data);
            } else if (event.event === "error") {
              throw new ApiError(500, event.detail);
            }
          }
          if (!gotResult) {
            // Stream closed without a result event — usually a sidecar
            // crash or a network hiccup. Surface it instead of silently
            // returning to a blank page.
            console.warn("[useOptimizeTeam] stream closed with no result event");
            throw new ApiError(500, "stream closed without result");
          }
        } catch (e) {
          console.error("[useOptimizeTeam] error", e);
          setError(e as Error);
        } finally {
          setPending(false);
        }
      })();
    },
    [],
  );

  return {
    mutate,
    data,
    error,
    isPending,
    isError: error !== null,
    progress,
  };
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
