import { Monitor, Moon, Sun } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { applyTheme, useThemeStore, type Theme } from "@/stores/theme";

const ORDER: Theme[] = ["system", "light", "dark"];
const ICON: Record<Theme, React.ComponentType<{ className?: string }>> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
};
const LABEL: Record<Theme, string> = {
  light: "Light",
  dark: "Dark",
  system: "System",
};

export function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  function cycle() {
    const next = ORDER[(ORDER.indexOf(theme) + 1) % ORDER.length];
    setTheme(next);
    applyTheme(next);
  }

  const Icon = ICON[theme];
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={cycle}
      title={`Theme: ${LABEL[theme]} — click to cycle`}
      aria-label={`Cycle theme (currently ${LABEL[theme]})`}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}
