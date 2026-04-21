const STORAGE_KEY = "lumina-forge:api-base-url";
// 31733 — Expedition 33 themed, sits in the IANA dynamic range so it
// avoids collisions with the usual dev-server default (8000).
const DEFAULT_API_BASE_URL = "http://127.0.0.1:31733";

export function getApiBaseUrl(): string {
  if (typeof window === "undefined") return DEFAULT_API_BASE_URL;
  return localStorage.getItem(STORAGE_KEY) ?? DEFAULT_API_BASE_URL;
}

export function setApiBaseUrl(url: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, url.replace(/\/+$/, ""));
}

export function resetApiBaseUrl(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

export { DEFAULT_API_BASE_URL };
