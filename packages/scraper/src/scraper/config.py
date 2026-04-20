"""Scraper-wide configuration: User-Agent, default paths, rate limits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scraper import __version__

USER_AGENT = f"lumina-forge/{__version__} (+https://github.com/Fievetl/lumina-forge)"


@dataclass(frozen=True, slots=True)
class Paths:
    """Resolved filesystem locations for a scrape run."""

    vault: Path
    cache: Path

    @classmethod
    def from_repo_root(cls, repo_root: Path) -> Paths:
        return cls(vault=repo_root / "vault", cache=repo_root / "cache")


@dataclass(frozen=True, slots=True)
class FetcherConfig:
    """Runtime knobs for the HttpFetcher."""

    user_agent: str = USER_AGENT
    requests_per_second: float = 1.0
    timeout_seconds: float = 30.0
    max_retries: int = 3
    refresh: bool = False  # when True, ignore cache and re-fetch
