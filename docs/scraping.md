# Adding a scraping source

> Stub — filled in during Phase 2.

## Checklist

1. Respect `robots.txt` and honour a 1 req/sec rate limit.
2. Set a descriptive `User-Agent` (`lumina-forge/<version> (+https://github.com/<user>/lumina-forge)`).
3. Cache raw HTML to `cache/<source-id>/<url-hash>.html` so re-runs don't re-fetch.
4. Implement a `SourceAdapter` subclass in `packages/scraper/src/scraper/sources/<source_id>.py`:
    - `fetch(self) -> Iterator[RawPage]`
    - `parse(self, page: RawPage) -> Iterator[VaultEntry]`
5. Register the adapter in `packages/scraper/src/scraper/sources/__init__.py`.
6. Add a unit test with a fixture HTML file covering the parsing logic.
7. Run `just scrape` — the new source writes into the vault on top of any existing entries; conflicting fields end up as a list under `sources:`.

## Sources in scope

- https://expedition33.wiki.fextralife.com — data exhaustive items / quests
- https://maxroll.gg/clair-obscur-expedition-33 — meta builds, formulas
- https://game8.co/games/Clair-Obscur-Expedition-33 — tier lists, guides
- https://www.clairbuilds.com — community builds
- https://www.expedition33builds.com — shared builds
- https://www.pictotracker.com — pictos data

## Dedupe strategy

Keyed by slug (e.g. `augmented-critical` for a picto). First source wins for scalar fields; list fields are merged. When scalar fields conflict, both values are kept — the frontmatter gets a `conflicts:` block with `{ field: [value_from_source_a, value_from_source_b] }` and the bodies are concatenated under headers naming the sources. This keeps everything human-auditable.
