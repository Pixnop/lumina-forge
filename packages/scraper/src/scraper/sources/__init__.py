"""Source adapters — one per website we scrape."""

from __future__ import annotations

from scraper.sources.base import EntryType, SourceAdapter
from scraper.sources.fextralife.adapter import FextralifeAdapter

# Registry — new adapters land here and become available via --source.
ADAPTERS: dict[str, type[SourceAdapter]] = {
    FextralifeAdapter.source_id: FextralifeAdapter,
}


def get_adapter(source_id: str) -> type[SourceAdapter]:
    try:
        return ADAPTERS[source_id]
    except KeyError as exc:
        known = ", ".join(sorted(ADAPTERS))
        raise KeyError(f"unknown source '{source_id}'. Known: {known}") from exc


__all__ = ["ADAPTERS", "EntryType", "FextralifeAdapter", "SourceAdapter", "get_adapter"]
