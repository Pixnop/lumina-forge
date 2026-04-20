import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "@/App";
import { applyTheme, useThemeStore } from "@/stores/theme";
import "@/styles.css";

// Apply the persisted theme before React mounts so there's no flash.
applyTheme(useThemeStore.getState().theme);

// Follow OS preference changes while the user is in "system" mode.
if (typeof window !== "undefined" && window.matchMedia) {
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => {
      if (useThemeStore.getState().theme === "system") {
        applyTheme("system");
      }
    });
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
