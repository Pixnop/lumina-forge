"""Parse the /Weapons index page.

The page has several ``wiki_table`` elements — one table per character
(Gustave, Maelle, Lune, etc.). Each character's table is preceded by a
heading that names them. Columns are:

    Name | Element | Power | Attributes | Passive Effects
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator

from bs4 import Tag

from scraper.models import RawPage, Weapon
from scraper.models.weapon import Passive, ScalingStat
from scraper.sources.fextralife.parsers._common import (
    cell_int,
    clean_text,
    data_rows,
    first_link,
    parse_html,
    slugify,
    wiki_tables,
)

log = logging.getLogger(__name__)

# "Vitality S Defense A" → scaling_stat ≈ the first letter-grade "S" stat.
_ATTR_TOKEN_RE = re.compile(r"([A-Za-z]+)\s+([SABCDF])")


def parse_weapons(page: RawPage) -> Iterator[Weapon]:
    soup = parse_html(page.html)
    tables = wiki_tables(soup)
    if not tables:
        log.warning("fextralife/weapon: no wiki_table found on %s", page.url)
        return

    for table in tables:
        character = _character_heading_for(table)
        for row in data_rows(table):
            cells = row.select("td")
            if len(cells) < 5:
                continue
            name, detail_url = first_link(cells[0])
            if not name:
                continue
            element, _ = first_link(cells[1])
            power = cell_int(cells[2].get_text(strip=True))
            attrs = _parse_attributes(cells[3].get_text(" ", strip=True))
            passives = _parse_passives(cells[4].get_text("\n", strip=True))
            sources: list[str] = []
            if detail_url:
                sources.append(detail_url)
            sources.append(str(page.url))
            yield Weapon(
                slug=slugify(name),
                name=name,
                character=character,
                base_damage=power,
                scaling_stat=_best_scaling(attrs),
                passives=passives,
                body=_build_body(element, attrs, passives),
                sources=sources,  # type: ignore[arg-type]
            )


def _character_heading_for(table: Tag) -> str | None:
    """Walk backwards to find the nearest heading naming the owner.

    Fextralife sometimes merges two characters into a single table (e.g.
    "Gustave & Verso All Weapons Comparison Table"). In that case we pick
    the *first* playable name mentioned in the heading so the weapon is at
    least assigned to someone — better than silently dropping it.
    """
    known = ["Gustave", "Lune", "Maelle", "Monoco", "Sciel", "Verso"]
    node = table.find_previous(["h2", "h3", "h4"])
    while node is not None:
        text = clean_text(node.get_text(" ", strip=True))
        low = text.lower()
        # Pick the name appearing earliest in the heading text.
        earliest_pos = len(text) + 1
        earliest_name: str | None = None
        for name in known:
            idx = low.find(name.lower())
            if idx != -1 and idx < earliest_pos:
                earliest_pos = idx
                earliest_name = name
        if earliest_name is not None:
            return earliest_name
        node = node.find_previous(["h2", "h3", "h4"])
    return None


def _parse_attributes(text: str) -> dict[str, str]:
    """Extract ``{'Vitality': 'S', 'Defense': 'A'}`` from 'Vitality S Defense A'."""
    cleaned = clean_text(text)
    return {stat: grade for stat, grade in _ATTR_TOKEN_RE.findall(cleaned)}


_SCALING_STATS: frozenset[ScalingStat] = frozenset(
    {"Might", "Agility", "Defense", "Luck", "Vitality"}
)


def _best_scaling(attrs: dict[str, str]) -> ScalingStat | None:
    """Return the stat with the highest scaling grade (S > A > B > C > D > F)."""
    order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}
    if not attrs:
        return None
    stat = min(attrs.items(), key=lambda kv: order.get(kv[1], 99))[0]
    # narrow str → Literal via an explicit match against the frozenset of valid stats
    for candidate in _SCALING_STATS:
        if candidate == stat:
            return candidate
    return None


def _parse_passives(text: str) -> list[Passive]:
    """Turn ``"Lvl. 4 : ... Lvl. 10 : ..."`` into a list of named Passive entries.

    Each passive's effect text is also fed through ``parse_effect_structured``
    so the optimizer sees weapon-level damage bonuses the same way it sees
    picto bonuses.
    """
    from scraper.sources.fextralife.parsers._effect import parse_effect_structured

    parts = re.split(r"(Lvl\.?\s*\d+\s*:)", text)
    passives: list[Passive] = []
    current_name = ""
    for chunk in parts:
        chunk = chunk.strip()
        if not chunk:
            continue
        if re.match(r"Lvl\.?\s*\d+\s*:", chunk):
            current_name = chunk.rstrip(":").strip()
        elif current_name:
            effect = clean_text(chunk)
            passives.append(
                Passive(
                    name=current_name,
                    effect=effect,
                    effect_structured=parse_effect_structured(effect),
                )
            )
            current_name = ""
    return passives


def _build_body(element: str | None, attrs: dict[str, str], passives: list[Passive]) -> str:
    lines: list[str] = []
    if element:
        lines.append(f"**Element:** {element}")
    if attrs:
        formatted = ", ".join(f"{k} {v}" for k, v in attrs.items())
        lines.append(f"**Scaling:** {formatted}")
    if passives:
        lines.append("\n**Passives**\n")
        for p in passives:
            lines.append(f"- *{p.name}* — {p.effect}")
    return "\n".join(lines)
