import { getApiBaseUrl } from "@/lib/config";
import type {
  HealthResponse,
  OptimizeRequest,
  OptimizeResponse,
  TeamOptimizeRequest,
  TeamOptimizeResponse,
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

export interface OptimizeProgressEvent {
  event: "progress";
  phase: string;
  pct: number;
}

export interface OptimizeResultEvent {
  event: "result";
  data: OptimizeResponse;
}

export interface OptimizeErrorEvent {
  event: "error";
  detail: string;
}

export type OptimizeStreamEvent =
  | OptimizeProgressEvent
  | OptimizeResultEvent
  | OptimizeErrorEvent;

export interface TeamOptimizeResultEvent {
  event: "result";
  data: TeamOptimizeResponse;
}

export type TeamStreamEvent =
  | OptimizeProgressEvent
  | TeamOptimizeResultEvent
  | OptimizeErrorEvent;

/**
 * Stream NDJSON events from POST /optimize/stream. The sidecar emits
 * one ``{"event": "progress", ...}`` per ~1 % of scoring work and a
 * single ``{"event": "result", ...}`` at the end. Errors arrive as
 * ``{"event": "error", "detail": ...}`` and the response then closes.
 *
 * Yields events as they arrive so the caller can update a progress bar
 * in real time.
 */
async function* ndjsonStream<T>(
  path: string,
  body: unknown,
): AsyncGenerator<T> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errBody = await response.json();
      if (typeof errBody?.detail === "string") detail = errBody.detail;
    } catch {
      // ignore non-JSON
    }
    throw new ApiError(response.status, detail);
  }
  const reader = response.body?.getReader();
  if (!reader) {
    // No streaming reader (older webviews, mocked envs). The response
    // is still NDJSON — read it all at once and yield line-by-line.
    const text = await response.text();
    for (const raw of text.split("\n")) {
      const line = raw.trim();
      if (line) yield JSON.parse(line) as T;
    }
    return;
  }
  const decoder = new TextDecoder();
  let buffer = "";
  // Drain the reader and emit on every newline. ``decoder.decode`` is
  // called with ``stream: true`` so a multi-byte UTF-8 sequence split
  // across chunks isn't garbled, then flushed with a final no-arg call
  // when ``done`` arrives — the previous version skipped that flush
  // and dropped the trailing chunk on payloads where the result event
  // landed in the same TCP packet as the close.
  while (true) {
    const { value, done } = await reader.read();
    if (value) buffer += decoder.decode(value, { stream: true });
    if (done) break;
    let nl = buffer.indexOf("\n");
    while (nl !== -1) {
      const line = buffer.slice(0, nl).trim();
      buffer = buffer.slice(nl + 1);
      nl = buffer.indexOf("\n");
      if (!line) continue;
      yield JSON.parse(line) as T;
    }
  }
  buffer += decoder.decode(); // flush
  for (const raw of buffer.split("\n")) {
    const line = raw.trim();
    if (line) yield JSON.parse(line) as T;
  }
}

async function* optimizeStream(
  body: OptimizeRequest,
): AsyncGenerator<OptimizeStreamEvent> {
  yield* ndjsonStream<OptimizeStreamEvent>("/optimize/stream", body);
}

async function* optimizeTeamStream(
  body: TeamOptimizeRequest,
): AsyncGenerator<TeamStreamEvent> {
  yield* ndjsonStream<TeamStreamEvent>("/optimize/team/stream", body);
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
  optimizeStream,
  optimizeTeam: (body: TeamOptimizeRequest) =>
    request<TeamOptimizeResponse>("/optimize/team", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  optimizeTeamStream,
};
