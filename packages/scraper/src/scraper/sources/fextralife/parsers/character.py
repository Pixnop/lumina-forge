"""Parse the /Characters index page — no table, heading-driven layout.

Each playable character gets an ``<h3>`` naming them, followed by a short
bulleted list with "Weapon Type", "Starting Weapon", "Starting Skills"
entries. We extract those into structured frontmatter and capture the
narrative paragraphs as the body.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from dataclasses import dataclass, field

from bs4 import Tag

from scraper.models import Character, RawPage
from scraper.sources.fextralife.parsers._common import (
    absolute_url,
    clean_text,
    parse_html,
    slugify,
)


@dataclass(slots=True)
class _CharacterBullets:
    weapon_type: str = ""
    starting_weapon: str = ""
    starting_skills: list[str] = field(default_factory=list)

log = logging.getLogger(__name__)

PLAYABLE = {"Gustave", "Lune", "Maelle", "Sciel", "Monoco", "Verso"}


def parse_characters(page: RawPage) -> Iterator[Character]:
    soup = parse_html(page.html)
    for h3 in soup.find_all("h3"):
        name = clean_text(h3.get_text(" ", strip=True))
        if name not in PLAYABLE:
            continue
        section = _collect_until_next_h3(h3)
        bullets = _parse_bullets(section)
        body = _build_body(section)
        yield Character(
            slug=slugify(name),
            name=name,
            signature_skills=bullets.starting_skills,
            archetypes=[bullets.weapon_type] if bullets.weapon_type else [],
            body=body,
            image_url=_first_portrait(section),  # type: ignore[arg-type]
            sources=[page.url],
        )


def _first_portrait(section: list[Tag]) -> str | None:
    """Pick the nearest character-portrait image from the section nodes."""
    for node in section:
        for img in node.find_all("img"):
            raw = img.get("data-src") or img.get("src")
            if not isinstance(raw, str):
                continue
            if "mhws.png" in raw or "logo" in raw.lower():
                continue
            if "Expedition-33" not in raw and "expedition-33" not in raw:
                continue
            return absolute_url(raw)
    return None


def _collect_until_next_h3(start: Tag) -> list[Tag]:
    collected: list[Tag] = []
    for sibling in start.next_siblings:
        if isinstance(sibling, Tag) and sibling.name == "h3":
            break
        if isinstance(sibling, Tag):
            collected.append(sibling)
    return collected


def _parse_bullets(section: list[Tag]) -> _CharacterBullets:
    """Pull "Weapon Type: X", "Starting Skills: X , Y" out of the first <ul>."""
    data = _CharacterBullets()
    for node in section:
        if node.name != "ul":
            continue
        for li in node.select("li"):
            text = clean_text(li.get_text(" ", strip=True))
            key_raw, _, value = text.partition(":")
            key = re.sub(r"\s+", "_", key_raw.strip().lower())
            value = clean_text(value)
            if not value:
                continue
            if "skill" in key:
                data.starting_skills.extend(
                    clean_text(part) for part in re.split(r"[,;]", value) if part.strip()
                )
            elif key == "weapon_type":
                data.weapon_type = value
            elif key == "starting_weapon":
                data.starting_weapon = value
        break  # only the first <ul> is the metadata bullet list
    return data


def _build_body(section: list[Tag]) -> str:
    paragraphs: list[str] = []
    for node in section:
        if node.name == "p":
            text = clean_text(node.get_text(" ", strip=True))
            if text and text != '"For those who come after."':
                paragraphs.append(text)
        if len(paragraphs) >= 3:
            break
    return "\n\n".join(paragraphs)
