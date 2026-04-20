import { getApiBaseUrl } from "@/lib/config";
import type {
  HealthResponse,
  OptimizeRequest,
  OptimizeResponse,
  VaultInfoResponse,
  VaultItemType,
  VaultItemsResponse,
} from "@/types/api";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(`API ${status}: ${detail}`);
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { "Content-Type": "application/json", ...init.headers },
    ...init,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (body?.detail) detail = JSON.stringify(body.detail);
    } catch {
      // ignore non-JSON error bodies
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  vaultInfo: () => request<VaultInfoResponse>("/vault/info"),
  vaultReload: () =>
    request<VaultInfoResponse>("/vault/reload", { method: "POST" }),
  vaultItems: (type: VaultItemType, character?: string) => {
    const params = new URLSearchParams({ type });
    if (character) params.set("character", character);
    return request<VaultItemsResponse>(`/vault/items?${params.toString()}`);
  },
  optimize: (body: OptimizeRequest) =>
    request<OptimizeResponse>("/optimize", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
