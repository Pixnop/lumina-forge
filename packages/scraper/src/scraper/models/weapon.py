"""Weapon vault entry."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from scraper.models.base import VaultEntry

ScalingStat = Literal["Might", "Agility", "Defense", "Luck", "Vitality"]


class Passive(BaseModel):
    name: str
    effect: str
    effect_structured: dict[str, object] = Field(default_factory=dict)


class Weapon(VaultEntry):
    folder: ClassVar[str] = "Weapons"
    type: ClassVar[str] = "weapon"

    character: str | None = None
    base_damage: int | None = None
    scaling_stat: ScalingStat | None = None
    boosted_skills: list[str] = Field(default_factory=list)
    passives: list[Passive] = Field(default_factory=list)
    upgrade_tree: dict[str, object] = Field(default_factory=dict)
    source_locations: list[dict[str, str]] = Field(default_factory=list)
