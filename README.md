# lumina-forge

Local tooling for **Clair Obscur: Expedition 33** randomizer runs: Obsidian knowledge base + web scrapers + build optimizer + desktop app.

Given the items you have right now (pictos, weapons, luminas, skills), the optimizer proposes the top builds per character, ranked by estimated DPS and utility. The knowledge base it reasons over lives as a human-readable Obsidian vault.

## Repo layout

| Path | What it is |
| --- | --- |
| `vault/` | Obsidian vault — open it directly in Obsidian |
| `packages/scraper/` | Python package that scrapes web sources into the vault |
| `packages/optimizer/` | Python package + FastAPI local service that ranks builds |
| `app/` | Desktop app (Tauri + React, arrives in Phase 4) |
| `docs/` | Contributor docs — architecture, how to add a scraping source |
| `.worktrees/` | Local git worktrees — gitignored |

## Prerequisites (Windows 11)

- Python 3.13
- [`uv`](https://docs.astral.sh/uv/) — `pip install uv` or `winget install astral-sh.uv`
- Node 20+ and [`pnpm`](https://pnpm.io/) — `npm i -g pnpm`
- [`just`](https://github.com/casey/just) — `winget install Casey.Just`
- [Obsidian](https://obsidian.md/) (only needed to browse the vault — the optimizer reads the markdown directly)

## Quickstart

```bash
just setup        # install Python + Node deps
just test         # run the Python test suite
just --list       # see all available commands
```

Open `vault/` as an Obsidian vault to browse the knowledge base.

## Phases

- **Phase 1** — scaffold (this commit): repo structure, empty vault, tooling skeleton
- **Phase 2** — scraping: Fextralife + Maxroll + Game8 + clair-builds into the vault
- **Phase 3** — optimizer: CLI-first, then FastAPI wrapper
- **Phase 4** — desktop app: Tauri + React

See [`docs/architecture.md`](docs/architecture.md) for the full design.

## License

MIT — see [`LICENSE`](LICENSE).
