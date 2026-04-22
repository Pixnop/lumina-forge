"""Picto vault entry."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from scraper.models.base import VaultEntry

PictoCategory = Literal["Offensive", "Defensive", "Utility"]
PictoTier = Literal["S", "A", "B", "C", "F"]


class Picto(VaultEntry):
    folder: ClassVar[str] = "Pictos"
    type: ClassVar[str] = "picto"

    category: PictoCategory | None = None
    tier: PictoTier | None = None
    effect: str = ""
    # Any because values are a mix of floats (damage_bonus, trigger_uptime, …)
    # and booleans (damage_cap_bypass, has_revive). Keep it permissive so new
    # keys can land without a schema change.
    effect_structured: dict[str, object] = Field(default_factory=dict)
    stats_granted: dict[str, int] = Field(default_factory=dict)
    lumina_after_mastery: str | None = None
    lumina_points_cost: int | None = None
    source_locations: list[dict[str, str]] = Field(default_factory=list)
