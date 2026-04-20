"""Core models shared by every entry type and the pipeline."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RawPage(BaseModel):
    """An HTTP response body paired with the URL it came from."""

    model_config = ConfigDict(frozen=True)

    source_id: str
    url: HttpUrl
    html: str
    fetched_at: datetime

    def cache_key(self) -> str:
        """Stable sha256 of the URL — used as the cache filename."""
        return hashlib.sha256(str(self.url).encode("utf-8")).hexdigest()


class VaultEntry(BaseModel):
    """Base class for anything that lands in the Obsidian vault.

    Subclasses declare their vault folder via the ``folder`` ClassVar, their
    entry ``type`` (also a ClassVar), and whatever typed fields the folder's
    ``_README.md`` says belongs in the frontmatter.
    """

    folder: ClassVar[str] = ""  # subclasses must override
    type: ClassVar[str] = ""  # subclasses must override

    slug: str = Field(description="kebab-case filename stem, unique within folder")
    name: str
    sources: list[HttpUrl] = Field(default_factory=list)
    body: str = ""

    def frontmatter(self) -> dict[str, object]:
        """Serialise typed fields to a YAML-serialisable dict.

        ``slug`` and ``body`` are *not* emitted — they belong to the file name
        and body respectively. Everything else goes to the frontmatter.
        """
        data = self.model_dump(mode="json", exclude={"slug", "body"})
        data["type"] = self.type
        data["sources"] = [str(u) for u in self.sources]
        # Drop empty optional fields to keep the frontmatter tidy. Preserve
        # explicit zeros and empty strings set by callers — only drop None and
        # truly empty containers.
        return {k: v for k, v in data.items() if v not in (None, [], {}, "")}


class ScrapeReport(BaseModel):
    """End-of-run summary shown to the user and written to cache/report.json."""

    model_config = ConfigDict(frozen=False)

    source_id: str
    pages_fetched: int = 0
    pages_from_cache: int = 0
    entries_created: int = 0
    entries_updated: int = 0
    entries_unchanged: int = 0
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
