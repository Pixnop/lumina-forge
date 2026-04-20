"""Parse the /Pictos index page.

The page has a single wiki_table with columns:
    Pictos Name | Affected Attributes | Luminas Effect | Lumina Points Cost
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from scraper.models import Picto, RawPage
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


def parse_pictos(page: RawPage) -> Iterator[Picto]:
    soup = parse_html(page.html)
    tables = wiki_tables(soup)
    if not tables:
        log.warning("fextralife/picto: no wiki_table found on %s", page.url)
        return

    for row in data_rows(tables[0]):
        cells = row.select("td")
        if len(cells) < 3:
            continue
        name, detail_url = first_link(cells[0])
        if not name:
            continue
        attrs_text = clean_text(cells[1].get_text(" ", strip=True))
        effect = clean_text(cells[2].get_text(" ", strip=True))
        pp_cost = cell_int(cells[3].get_text(strip=True)) if len(cells) > 3 else None
        sources: list[str] = []
        if detail_url:
            sources.append(detail_url)
        sources.append(str(page.url))
        yield Picto(
            slug=slugify(name),
            name=name,
            effect=effect,
            stats_granted=_parse_attributes(attrs_text),
            lumina_points_cost=pp_cost,
            sources=sources,  # type: ignore[arg-type]  # pydantic coerces str -> HttpUrl
        )


def _parse_attributes(text: str) -> dict[str, int]:
    """Turn ``"Health , Speed , Critical Rate"`` into ``{'Health': 0, ...}``.

    The index page only lists *which* stats a picto grants — magnitudes live
    on detail pages, which Phase 2 doesn't fetch. We record the names with a
    0 sentinel so downstream consumers know the stats exist.
    """
    if not text:
        return {}
    return {part.strip(): 0 for part in text.split(",") if part.strip()}
