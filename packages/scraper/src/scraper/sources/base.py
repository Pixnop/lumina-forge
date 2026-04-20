"""Source adapter contract."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Literal, Protocol, runtime_checkable

from scraper.fetch import HttpFetcher
from scraper.models import RawPage, VaultEntry

EntryType = Literal["character", "picto", "weapon", "lumina", "skill"]


@runtime_checkable
class SourceAdapter(Protocol):
    """Contract every source implementation must satisfy.

    An adapter discovers URLs for the entry types the orchestrator asks for,
    and turns raw pages into VaultEntry objects. It *never* writes to the
    vault and *never* manages HTTP state — those belong to the merger and
    fetcher respectively.
    """

    source_id: str

    def discover(
        self, fetcher: HttpFetcher, entry_types: list[EntryType]
    ) -> Iterator[tuple[EntryType, str]]:
        """Yield ``(entry_type, url)`` pairs worth parsing.

        For index-page sources, implementers typically fetch the index once
        and yield every detail link plus the index URL itself.
        """
        ...

    def parse(self, entry_type: EntryType, page: RawPage) -> Iterator[VaultEntry]:
        """Turn a fetched page into zero or more VaultEntry objects."""
        ...
