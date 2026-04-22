"""Skill vault entry."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from scraper.models.base import VaultEntry

SkillCategory = Literal["Offensive", "Defensive", "Utility", "Buff", "Debuff"]
Targeting = Literal["SingleEnemy", "AllEnemies", "Self", "Ally", "AllAllies"]
Element = Literal["Neutral", "Fire", "Ice", "Lightning", "Dark", "Light", "Earth"]


class DamageSpec(BaseModel):
    formula: str | None = None
    base: int | None = None
    multiplier_stat: str | None = None
    hits: int | None = None
    scaling_notes: str | None = None


class StatusApplication(BaseModel):
    name: str
    chance: float | None = None
    duration: int | None = None


class Skill(VaultEntry):
    folder: ClassVar[str] = "Skills"
    type: ClassVar[str] = "skill"

    character: str | None = None
    ap_cost: int | None = None
    ap_generated: int | None = None
    category: SkillCategory | None = None
    targeting: Targeting | None = None
    element: Element | None = None
    hits: int | None = None
    damage: DamageSpec | None = None
    status_applied: list[StatusApplication] = Field(default_factory=list)
    cooldown: int | None = None
