# app/

Phase 4 deliverable — Tauri + React desktop app. Empty on purpose right now.

Planned screens:

1. **Inventory** — enter what you have, with autocomplete from the vault
2. **Optimize** — pick character + parameters, get top-5 builds
3. **Build Detail** — drill into one ranked build (stats, rotation, synergy explanation)
4. **Knowledge Base Browser** — read-only markdown view of the vault
5. **Settings** — vault path, re-scrape trigger

The app talks to a local FastAPI service spawned by the optimizer package.
