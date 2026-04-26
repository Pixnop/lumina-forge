# Future work — things on the roadmap that need a fresh session

## Maxroll community-planner scraper

**Status**: blocked without a browser runtime.

Exploration done in the v0.7.0 session confirmed:

- `/clair-obscur-expedition-33/planner/community-builds` is a pure SPA.
  The initial HTML has no `__NEXT_DATA__`, no Remix hydration state, no
  `<a>` links to individual builds.
- Networked requests from the page are limited to `/api/me`,
  `/api/twitch`, analytics beacons — no build-list endpoint is visible.
- The 2 static `/guides/*` articles we already hand-transcribed (Early
  Game Expert + Endgame Burn Stacking) cover ~7 builds with high fidelity.

Paths forward when someone comes back to this:

1. **Runtime Playwright adapter** — add Playwright as a `scraper`
   dependency (bundle ~200 MB), render the planner headlessly, scrape
   the hydrated DOM. Heavy infra for ~20-50 user-submitted builds of
   uneven quality.
2. **Reverse-engineer the GraphQL endpoint** — the page must fetch
   builds from *somewhere*; capture the call with devtools, replay it
   in Python. Fragile: any backend redeploy can rotate the schema.
3. **Let users drop in their own Maxroll build export** — if Maxroll
   publishes a "share" JSON export, parse that client-side and write
   to `vault/Builds/`. Lowest-effort, assumes feature exists.

## Inventory auto-detect from save files

**Status**: needs Expedition 33's actual save format first.

The save file lives at `%LOCALAPPDATA%\Sandfall\Saved\SaveGames\` on
Windows but the format is not documented — likely a proprietary
binary blob produced by Unreal Engine's SaveGame subsystem.

Work needed:

1. Reverse-engineer the .sav format (likely `FObjectAndNameAsStringProxyArchive`)
2. Map the in-game inventory state to our `Inventory` schema
3. Add a file-picker UI in the React app that reads the save → populates
   the inventory draft

This is a one-off effort of uncertain difficulty. Better done as a
dedicated side project than a single roadmap item.
