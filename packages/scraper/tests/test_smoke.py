"""Smoke test — confirms the scraper package imports and ships a version."""

from __future__ import annotations

import scraper


def test_package_has_version() -> None:
    assert scraper.__version__ == "0.1.0"
