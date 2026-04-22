"""Parse the /Skills index page.

Columns: Name | AP Cost | Character | Prerequisite | Skill Effect
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator

from scraper.models import RawPage, Skill
from scraper.sources.fextralife.parsers._common import (
    cell_int,
    clean_text,
    data_rows,
    first_link,
    parse_html,
    row_image_url,
    slugify,
    wiki_tables,
)

log = logging.getLogger(__name__)

_HITS_RE = re.compile(r"(\d+)\s+hits?\b", re.I)


def parse_skills(page: RawPage) -> Iterator[Skill]:
    soup = parse_html(page.html)
    tables = wiki_tables(soup)
    if not tables:
        log.warning("fextralife/skill: no wiki_table found on %s", page.url)
        return

    for row in data_rows(tables[0]):
        cells = row.select("td")
        if len(cells) < 5:
            continue
        name, detail_url = first_link(cells[0])
        if not name:
            continue
        ap_cost = cell_int(cells[1].get_text(strip=True))
        character_name, _ = first_link(cells[2])
        effect = clean_text(cells[4].get_text(" ", strip=True))
        body = _build_body(cells[3], effect)
        sources: list[str] = []
        if detail_url:
            sources.append(detail_url)
        sources.append(str(page.url))
        hits_match = _HITS_RE.search(effect)
        hits = int(hits_match.group(1)) if hits_match else None
        yield Skill(
            slug=slugify(name),
            name=name,
            character=character_name,
            ap_cost=ap_cost,
            hits=hits,
            body=body,
            image_url=row_image_url(row),  # type: ignore[arg-type]
            sources=sources,  # type: ignore[arg-type]
        )


def _build_body(prerequisite_cell: object, effect: str) -> str:
    from bs4 import Tag

    prereq_text = ""
    if isinstance(prerequisite_cell, Tag):
        prereq_text = clean_text(prerequisite_cell.get_text(" ", strip=True))

    parts: list[str] = []
    if effect:
        parts.append(f"**Effect**\n\n{effect}")
    if prereq_text:
        parts.append(f"**Prerequisite:** {prereq_text}")
    return "\n\n".join(parts)
