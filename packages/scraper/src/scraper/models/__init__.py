"""Pydantic models: what flows between adapters and the vault merger."""

from __future__ import annotations

from scraper.models.base import RawPage, ScrapeReport, VaultEntry
from scraper.models.character import Character
from scraper.models.lumina import Lumina
from scraper.models.picto import Picto
from scraper.models.skill import DamageSpec, Skill, StatusApplication
from scraper.models.weapon import Passive, Weapon

ENTRY_TYPES: dict[str, type[VaultEntry]] = {
    "character": Character,
    "picto": Picto,
    "weapon": Weapon,
    "lumina": Lumina,
    "skill": Skill,
}

__all__ = [
    "ENTRY_TYPES",
    "Character",
    "DamageSpec",
    "Lumina",
    "Passive",
    "Picto",
    "RawPage",
    "ScrapeReport",
    "Skill",
    "StatusApplication",
    "VaultEntry",
    "Weapon",
]
