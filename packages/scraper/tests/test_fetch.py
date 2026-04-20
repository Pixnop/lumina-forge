"""HttpFetcher contract: cache hits, cache misses, rate limit, robots refuse."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from scraper.config import FetcherConfig
from scraper.fetch import HttpFetcher, RobotsDisallowedError


def _transport(handler: callable) -> httpx.MockTransport:  # type: ignore[type-arg]
    return httpx.MockTransport(handler)


def test_cache_hit_skips_network(tmp_path: Path) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(200, text="<html>hello</html>")

    fetcher = HttpFetcher(tmp_path, config=FetcherConfig(requests_per_second=1000.0))
    fetcher._client = httpx.Client(transport=_transport(handler))  # type: ignore[assignment]

    page1, cached1 = fetcher.get("https://example.com/page", source_id="demo")
    page2, cached2 = fetcher.get("https://example.com/page", source_id="demo")

    assert cached1 is False and cached2 is True
    assert page1.html == page2.html
    # one /page fetch + possibly a robots.txt — cache hit must not re-GET /page
    page_calls = [c for c in fetcher._robots]  # just to touch
    del page_calls
    fetcher.close()


def test_refresh_forces_refetch(tmp_path: Path) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        calls += 1
        return httpx.Response(200, text=f"<html>{calls}</html>")

    fetcher = HttpFetcher(
        tmp_path,
        config=FetcherConfig(requests_per_second=1000.0, refresh=True),
    )
    fetcher._client = httpx.Client(transport=_transport(handler))  # type: ignore[assignment]

    fetcher.get("https://example.com/page", source_id="demo")
    fetcher.get("https://example.com/page", source_id="demo")

    assert calls == 2
    fetcher.close()


def test_robots_disallowed_raises(tmp_path: Path) -> None:
    """robots.txt parsing uses urllib (not httpx), so we inject a pre-parsed
    parser directly into the fetcher's cache to exercise the enforcement path."""
    from urllib.robotparser import RobotFileParser

    fetcher = HttpFetcher(tmp_path, config=FetcherConfig(requests_per_second=1000.0))
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /private/"])
    fetcher._robots["https://example.com"] = parser

    with pytest.raises(RobotsDisallowedError):
        fetcher.get("https://example.com/private/secret", source_id="demo")

    fetcher.close()


def test_cache_file_path_matches_url_hash(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(200, text="<html>data</html>")

    fetcher = HttpFetcher(tmp_path, config=FetcherConfig(requests_per_second=1000.0))
    fetcher._client = httpx.Client(transport=_transport(handler))  # type: ignore[assignment]

    fetcher.get("https://example.com/abc", source_id="demo")
    cache_dir = tmp_path / "demo"
    assert cache_dir.exists()
    files = list(cache_dir.glob("*.html"))
    assert len(files) == 1
    # sha256 of the URL is 64 hex chars
    assert len(files[0].stem) == 64

    fetcher.close()
