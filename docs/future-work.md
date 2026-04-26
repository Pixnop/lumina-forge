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

**Status**: confirmed feasible; needs a dedicated session.

Save files live at:

```
%LOCALAPPDATA%\Sandfall\Saved\SaveGames\<steam-id>\EXPEDITION_<n>.sav
```

Investigation in the v0.7.0 session confirmed:

- Files are **GVAS** format (Unreal Engine `USaveGame`), magic `b"GVAS"`
  in the first 4 bytes.
- Stringtable contains the structural names we need:
  `/Game/Gameplay/Inventory/FEquipmentSlot`,
  `/Game/Gameplay/Pictos/Weapons/S_WeaponInstanceHandle`,
  `/Game/Gameplay/CharacterData/E_CharacterList`,
  `CharactersCollection`, `CARD_Pictos`, `CARD_Lumina`, `CARD_SkillCard`,
  `ECharacterAttribute::NewEnumerator0..4` (Might/Agi/Def/Luck/Vit).
- Items themselves are stored as **opaque asset handles** — internal
  Unreal IDs, not the human-readable slugs in our vault. A naive
  string scan finds maybe 6-14 distinct slugs out of 600+ vault entries
  and most are coincidental fragments.

Work needed for a real importer:

1. **GVAS property parser** — string FNames + property type tags +
   nested struct/array recursion. ~400 LoC of careful binary work.
   References: `gvas-converter` (Rust), `uesave-rs` (Rust). No usable
   Python package on PyPI as of this writing.
2. **Asset handle → slug mapping** — build by either
   (a) unpacking the game's `.pak` files with `repak`/`umodel` and
   reading the data tables, or
   (b) instrumenting a small Tauri command that the user runs once
   per item to record `handle → slug`.
3. **Tauri command + React file-picker** — read the chosen save,
   resolve handles, populate the `Inventory` draft.

Conservative estimate: a full session for the parser + a second
session for the mapping. Not bigger, not smaller.
