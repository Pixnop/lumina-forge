"""Character vault entry — one of the 6 playable Expedition 33 characters."""

from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from scraper.models.base import VaultEntry

CharacterRole = Literal["Offensive", "Defensive", "Support", "Hybrid"]


class Character(VaultEntry):
    folder: ClassVar[str] = "Characters"
    type: ClassVar[str] = "character"

    role: CharacterRole | None = None
    primary_stat: str | None = None
    signature_skills: list[str] = Field(default_factory=list)
    archetypes: list[str] = Field(default_factory=list)
    base_stats: dict[str, int] = Field(default_factory=dict)
