"""Parse the /Luminas index page.

Each row maps to the *mastered-picto* lumina form: name, effect, PP cost.
Every Lumina is derived from a same-named Picto, so we link via
``source_picto = <slug>`` to keep the vault graph tight.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

from scraper.models import Lumina, RawPage
from scraper.sources.fextralife.parsers._common import (
    cell_int,
    clean_text,
    data_rows,
    first_link,
    parse_html,
    slugify,
    wiki_tables,
)
from scraper.sources.fextralife.parsers._effect import parse_effect_structured

log = logging.getLogger(__name__)


def parse_luminas(page: RawPage) -> Iterator[Lumina]:
    soup = parse_html(page.html)
    tables = wiki_tables(soup)
    if not tables:
        log.warning("fextralife/lumina: no wiki_table found on %s", page.url)
        return

    for row in data_rows(tables[0]):
        cells = row.select("td")
        if len(cells) < 2:
            continue
        name, detail_url = first_link(cells[0])
        if not name:
            continue
        effect = clean_text(cells[1].get_text(" ", strip=True))
        pp_cost = cell_int(cells[2].get_text(strip=True)) if len(cells) > 2 else None
        slug = slugify(name)
        sources: list[str] = []
        if detail_url:
            sources.append(detail_url)
        sources.append(str(page.url))
        yield Lumina(
            slug=slug,
            name=name,
            effect=effect,
            effect_structured=parse_effect_structured(effect),
            pp_cost=pp_cost,
            source_picto=slug,
            sources=sources,  # type: ignore[arg-type]
        )
