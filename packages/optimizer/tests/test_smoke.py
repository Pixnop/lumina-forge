"""Smoke test — confirms the optimizer package imports and ships a version."""

from __future__ import annotations

import optimizer


def test_package_has_version() -> None:
    assert optimizer.__version__ == "0.8.2"
