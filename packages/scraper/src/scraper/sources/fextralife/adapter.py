"""FextralifeAdapter — index-page driven discovery for Expedition 33."""

from __future__ import annotations

import logging
from collections.abc import Iterator

from scraper.fetch import HttpFetcher
from scraper.models import RawPage, VaultEntry
from scraper.sources.base import EntryType
from scraper.sources.fextralife.parsers import PARSERS

log = logging.getLogger(__name__)

INDEX_URLS: dict[EntryType, str] = {
    "picto": "https://expedition33.wiki.fextralife.com/Pictos",
    "weapon": "https://expedition33.wiki.fextralife.com/Weapons",
    "lumina": "https://expedition33.wiki.fextralife.com/Luminas",
    "skill": "https://expedition33.wiki.fextralife.com/Skills",
    "character": "https://expedition33.wiki.fextralife.com/Characters",
}


class FextralifeAdapter:
    """Each entry type maps to a single index page containing all rows.

    We don't crawl detail pages in Phase 2 — the index tables carry enough
    data to fill a useful ~80% of the vault. Detail enrichment can land as
    a follow-up by extending ``discover`` to yield detail URLs.
    """

    source_id = "fextralife"

    def discover(
        self, fetcher: HttpFetcher, entry_types: list[EntryType]
    ) -> Iterator[tuple[EntryType, str]]:
        for et in entry_types:
            url = INDEX_URLS.get(et)
            if url is None:
                log.warning("fextralife: no index URL for entry type %r — skipping", et)
                continue
            yield et, url

    def parse(self, entry_type: EntryType, page: RawPage) -> Iterator[VaultEntry]:
        parser = PARSERS.get(entry_type)
        if parser is None:
            log.warning("fextralife: no parser registered for %r — skipping", entry_type)
            return
        yield from parser(page)
