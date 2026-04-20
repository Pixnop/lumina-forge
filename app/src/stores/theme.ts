import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | "system";

interface ThemeState {
  theme: Theme;
  setTheme: (next: Theme) => void;
  /** Read the actual mode taking system preference into account. */
  resolvedTheme: () => "light" | "dark";
}

function systemPrefersDark(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: "system",
      setTheme: (theme) => set({ theme }),
      resolvedTheme: () => {
        const { theme } = get();
        if (theme === "system") return systemPrefersDark() ? "dark" : "light";
        return theme;
      },
    }),
    { name: "lumina-forge:theme" },
  ),
);

/** Apply the resolved theme to <html class>. Call from the app bootstrap. */
export function applyTheme(theme: Theme): void {
  const resolved =
    theme === "system" ? (systemPrefersDark() ? "dark" : "light") : theme;
  const root = document.documentElement;
  root.classList.toggle("dark", resolved === "dark");
}
