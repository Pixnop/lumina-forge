"""Shared pytest fixtures for the scraper test suite."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from scraper.models import RawPage

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fextralife_fixture() -> callable[[str], RawPage]:  # type: ignore[type-arg]
    """Build a RawPage from a fixture filename (without extension)."""

    def _build(name: str) -> RawPage:
        path = FIXTURES_DIR / "fextralife" / f"{name}.html"
        html = path.read_text(encoding="utf-8")
        url = f"https://expedition33.wiki.fextralife.com/{name.removeprefix('index_').capitalize()}"
        return RawPage(
            source_id="fextralife",
            url=url,  # type: ignore[arg-type]
            html=html,
            fetched_at=datetime(2026, 4, 20, 12, 0, 0),
        )

    return _build
