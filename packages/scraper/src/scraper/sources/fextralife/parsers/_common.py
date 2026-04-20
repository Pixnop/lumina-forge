"""Shared parsing helpers for Fextralife pages."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

BASE_URL = "https://expedition33.wiki.fextralife.com"

# Fextralife sometimes flags rows with "- NEW ! Thank You Update DLC" — we
# strip these noise markers from names so slugs stay stable.
_NEW_MARKER_RE = re.compile(r"\s*-\s*NEW\s*!?\s*.*$", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def clean_text(raw: str | None) -> str:
    """Collapse whitespace + strip NBSP + trim."""
    if not raw:
        return ""
    return _WHITESPACE_RE.sub(" ", raw.replace("\xa0", " ")).strip()


def clean_name(raw: str) -> str:
    """Strip marketing markers ('NEW ! ...') that appear in Fextralife names."""
    return _NEW_MARKER_RE.sub("", clean_text(raw)).strip()


def slugify(name: str) -> str:
    """Turn 'Double Third' into 'double-third'."""
    text = clean_name(name).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def absolute_url(href: str | None) -> str | None:
    """Resolve Fextralife-relative links against the wiki base URL."""
    if not href:
        return None
    if urlparse(href).scheme:
        return href
    return urljoin(BASE_URL + "/", href.lstrip("/"))


def first_link(cell: Tag) -> tuple[str | None, str | None]:
    """Return (name, absolute_url) from the first <a> in a cell, or (text, None)."""
    link = cell.select_one("a[href]")
    if link is None:
        return clean_name(cell.get_text(" ", strip=True)) or None, None
    href = link.get("href")
    href_str = href if isinstance(href, str) else None
    return clean_name(link.get_text(" ", strip=True)) or None, absolute_url(href_str)


def wiki_tables(soup: BeautifulSoup) -> list[Tag]:
    return list(soup.select("table.wiki_table"))


def table_headers(table: Tag) -> list[str]:
    header_row = table.select_one("tr")
    if header_row is None:
        return []
    return [clean_text(h.get_text(" ", strip=True)) for h in header_row.select("th, td")]


def data_rows(table: Tag) -> list[Tag]:
    """Yield rows that have ``<td>`` cells (skipping header rows)."""
    return [tr for tr in table.select("tr") if tr.select("td")]


def cell_int(text: str) -> int | None:
    match = re.search(r"-?\d+", text)
    return int(match.group(0)) if match else None
