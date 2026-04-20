# Adding a scraping source

The pipeline is **source-agnostic**: the fetcher (rate limit + cache + robots.txt), the merger (dedupe + write) and the CLI are shared across sources. Adding a new source is three files plus a registry entry.

## Checklist

1. Decide which entry types the source will produce (`picto`, `weapon`, `lumina`, `skill`, `character`).
2. Create `packages/scraper/src/scraper/sources/<source_id>/` with an `adapter.py` implementing the `SourceAdapter` protocol:
    - `source_id: str` class attribute
    - `discover(fetcher, entry_types) -> Iterator[tuple[EntryType, str]]`
    - `parse(entry_type, page) -> Iterator[VaultEntry]`
3. Add per-type parsers under `sources/<source_id>/parsers/<type>.py`. Each parser takes a `RawPage` and yields `VaultEntry` subclasses.
4. Register the adapter in `packages/scraper/src/scraper/sources/__init__.py`.
5. Snapshot a few pages from the source into `packages/scraper/tests/fixtures/<source_id>/` and write parser unit tests that load them.
6. Run `just scrape --source <source_id>` — the new source writes on top of any existing entries; conflicting scalars land under `conflicts:` in the frontmatter, lists are unioned, bodies gain a `## Notes — <source_url>` section.

## Platform guarantees

- **Rate limit**: 1 req/sec per domain by default. Tunable via `FetcherConfig.requests_per_second`.
- **User-Agent**: `lumina-forge/<version> (+https://github.com/Fievetl/lumina-forge)`.
- **Cache**: raw HTML at `cache/<source_id>/<sha256-of-url>.html`. `--refresh` ignores the cache.
- **robots.txt**: checked once per origin, enforced on every URL. Disallowed URLs raise `RobotsDisallowedError` and are recorded in the `ScrapeReport` without aborting the run.
- **Error isolation**: a failed page fetch or parse is logged and counted; the run continues with the next URL.

## Sources in scope

| Source | Status |
| --- | --- |
| [Fextralife](https://expedition33.wiki.fextralife.com) | ✅ Phase 2 — index-page driven, ~700 entries |
| [Maxroll](https://maxroll.gg/clair-obscur-expedition-33) | planned |
| [Game8](https://game8.co/games/Clair-Obscur-Expedition-33) | planned |
| [Clair Builds](https://www.clairbuilds.com) | planned |
| [Expedition33 Builds](https://www.expedition33builds.com) | planned |
| [Picto Tracker](https://www.pictotracker.com) | planned |

## Dedupe strategy

Keyed by slug (e.g. `augmented-critical` for a picto). The merger never overwrites a scalar silently:

- **scalars in disagreement** → original value stays as the "surface" value, both values are recorded under `conflicts.<field>` as a list of `{value, source}` objects.
- **list fields** → unioned with insertion order preserved.
- **dict fields** → merged key by key; inner-key conflicts land under `conflicts.<outer-field>.<inner-field>`.
- **`sources` field** → appended, dedup by URL.
- **body text** → existing content is preserved; each new source appends a `## Notes — <source_url>` section with its text.

This keeps everything human-auditable.
