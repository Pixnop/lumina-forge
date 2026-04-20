"""Lumina vault entry."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from scraper.models.base import VaultEntry

LuminaCategory = Literal["Offensive", "Defensive", "Utility"]


class Lumina(VaultEntry):
    folder: ClassVar[str] = "Luminas"
    type: ClassVar[str] = "lumina"

    pp_cost: int | None = None
    category: LuminaCategory | None = None
    effect: str = ""
    effect_structured: dict[str, object] = Field(default_factory=dict)
    restrictions: list[str] = Field(default_factory=list)
    source_picto: str | None = None
