"""HTTP fetching with disk cache, per-domain rate limiting and robots.txt."""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Self
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from scraper.config import FetcherConfig
from scraper.models import RawPage

log = logging.getLogger(__name__)


class RobotsDisallowedError(RuntimeError):
    """Raised when robots.txt forbids a URL we were about to fetch."""


class HttpFetcher:
    """Rate-limited HTTP client with disk cache and robots.txt enforcement.

    One fetcher instance spans a whole scrape run. Per-domain rate limits are
    enforced (1 req/s by default), a sha256-of-URL keyed cache lives at
    ``cache/<source_id>/<hash>.html``, and ``robots.txt`` is consulted once
    per domain and checked for every URL we touch.
    """

    def __init__(self, cache_dir: Path, config: FetcherConfig | None = None) -> None:
        self._cache_dir = cache_dir
        self._config = config or FetcherConfig()
        self._client = httpx.Client(
            headers={"User-Agent": self._config.user_agent},
            timeout=self._config.timeout_seconds,
            follow_redirects=True,
        )
        self._last_request_at: dict[str, float] = {}
        self._robots: dict[str, RobotFileParser] = {}

    # --- context management -------------------------------------------------

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # --- public API ---------------------------------------------------------

    def get(self, url: str, *, source_id: str) -> tuple[RawPage, bool]:
        """Return (page, from_cache).

        Raises :class:`RobotsDisallowedError` if the URL is forbidden.
        """
        self._assert_allowed(url)
        cache_path = self._cache_path(source_id, url)

        if not self._config.refresh and cache_path.exists():
            html = cache_path.read_text(encoding="utf-8")
            return self._build_page(source_id, url, html), True

        html = self._fetch_with_rate_limit(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(html, encoding="utf-8")
        return self._build_page(source_id, url, html), False

    # --- internals ----------------------------------------------------------

    def _cache_path(self, source_id: str, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._cache_dir / source_id / f"{digest}.html"

    def _build_page(self, source_id: str, url: str, html: str) -> RawPage:
        return RawPage(
            source_id=source_id,
            url=url,  # type: ignore[arg-type]  # HttpUrl coerces from str
            html=html,
            fetched_at=datetime.now(),
        )

    def _assert_allowed(self, url: str) -> None:
        parser = self._get_robots_parser(url)
        if not parser.can_fetch(self._config.user_agent, url):
            raise RobotsDisallowedError(f"robots.txt forbids {url}")

    def _get_robots_parser(self, url: str) -> RobotFileParser:
        origin = self._origin(url)
        if origin not in self._robots:
            parser = RobotFileParser()
            parser.set_url(f"{origin}/robots.txt")
            try:
                parser.read()
            except Exception as exc:
                log.warning("robots.txt fetch failed for %s: %s — allowing by default", origin, exc)
                parser.parse([])
            self._robots[origin] = parser
        return self._robots[origin]

    @staticmethod
    def _origin(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _rate_limit(self, origin: str) -> None:
        min_gap = 1.0 / self._config.requests_per_second
        last = self._last_request_at.get(origin, 0.0)
        now = time.monotonic()
        elapsed = now - last
        if elapsed < min_gap:
            time.sleep(min_gap - elapsed)
        self._last_request_at[origin] = time.monotonic()

    def _fetch_with_rate_limit(self, url: str) -> str:
        origin = self._origin(url)
        self._rate_limit(origin)
        return self._do_http_get(url)

    @retry(
        reraise=True,
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def _do_http_get(self, url: str) -> str:
        log.info("GET %s", url)
        response = self._client.get(url)
        response.raise_for_status()
        return response.text
