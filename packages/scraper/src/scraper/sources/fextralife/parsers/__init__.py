"""Fextralife per-entry-type parsers."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from scraper.models import RawPage, VaultEntry
from scraper.sources.base import EntryType
from scraper.sources.fextralife.parsers.character import parse_characters
from scraper.sources.fextralife.parsers.lumina import parse_luminas
from scraper.sources.fextralife.parsers.picto import parse_pictos
from scraper.sources.fextralife.parsers.skill import parse_skills
from scraper.sources.fextralife.parsers.weapon import parse_weapons

ParserFn = Callable[[RawPage], Iterator[VaultEntry]]

PARSERS: dict[EntryType, ParserFn] = {
    "picto": parse_pictos,
    "weapon": parse_weapons,
    "lumina": parse_luminas,
    "skill": parse_skills,
    "character": parse_characters,
}

__all__ = [
    "PARSERS",
    "ParserFn",
    "parse_characters",
    "parse_luminas",
    "parse_pictos",
    "parse_skills",
    "parse_weapons",
]
