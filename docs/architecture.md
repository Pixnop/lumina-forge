# Architecture

```
+-------------+         +------------------+         +---------------+
|   Sources   |  ---->  |     scraper/     |  ---->  |    vault/     |
| (Fextralife,|         | (Python, httpx,  |         | (Obsidian     |
|  Maxroll,   |         |  bs4, dedupe,    |         |  markdown +   |
|  Game8, …)  |         |  cache on disk)  |         |  YAML front-  |
+-------------+         +------------------+         |  matter)      |
                                                     +-------+-------+
                                                             |
                                                             v
                                                   +-------------------+
                                                   |    optimizer/     |
                                                   | (loads vault,     |
                                                   |  enumerates       |
                                                   |  builds, scores,  |
                                                   |  ranks top N)     |
                                                   +---------+---------+
                                                             |
                                                             v
                                                    +------------------+
                                                    |   FastAPI local  |
                                                    |   service        |
                                                    +--------+---------+
                                                             |
                                                             v
                                                    +------------------+
                                                    |      app/        |
                                                    | (Tauri + React)  |
                                                    +------------------+
```

## Data flow

1. The **scraper** fetches HTML from configured sources, caches raw pages on disk, parses structured fields, and writes (or updates) notes under `vault/Pictos/`, `vault/Weapons/`, etc. Dedupe happens at the slug level; conflicting values from different sources are kept as a list in the `sources:` frontmatter.
2. The **vault** is the single source of truth. Obsidian can open it for human browsing, and it's also the input format the optimizer reads. YAML frontmatter carries the machine-readable fields; body text is for humans.
3. The **optimizer** loads the vault once at startup, builds in-memory indices (by character, by component type, by synergy) and serves ranking queries. The core is pure Python + `pydantic` models; the API layer is `FastAPI`.
4. The **app** talks to the local FastAPI over HTTP (or Tauri IPC as a second channel for commands like "re-scrape"). The app renders the inventory form, the ranking, and a read-only markdown view of the vault.

## Phase boundaries

| Phase | Scope | Acceptance criteria |
| --- | --- | --- |
| 1 | Scaffold | Repo layout + empty vault + tooling works — **this phase** |
| 2 | Scraping | At least Fextralife + Maxroll populate the vault with valid frontmatter |
| 3 | Optimizer | CLI ranks top N builds from a JSON inventory; FastAPI serves the same |
| 4 | Desktop app | Tauri app wraps the API and is packaged as an `.exe` |

## Decisions

- **Python for the backend** — best libraries for markdown + HTML parsing and for numerical scoring.
- **uv workspace** — `scraper/` and `optimizer/` are separate installable packages so they can be developed and tested in isolation.
- **Tauri over Electron** — smaller binary, native Windows feel. Electron is the fallback if Tauri blocks us.
- **Everything local** — no cloud, no telemetry. The scraper respects `robots.txt` and rate-limits at 1 rps.
- **Vault = source of truth** — we don't maintain a separate SQLite or JSON store. Parse markdown at optimizer startup; cache the parsed indices in memory.
