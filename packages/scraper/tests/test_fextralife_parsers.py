"""Parser contracts against live-scraped Fextralife fixture HTML."""

from __future__ import annotations

from scraper.models import Character, Lumina, Picto, Skill, Weapon
from scraper.sources.fextralife.parsers import (
    parse_characters,
    parse_luminas,
    parse_pictos,
    parse_skills,
    parse_weapons,
)


def test_picto_parser_yields_many_entries(fextralife_fixture) -> None:  # type: ignore[no-untyped-def]
    page = fextralife_fixture("index_pictos")
    entries = list(parse_pictos(page))
    assert len(entries) > 150
    assert all(isinstance(e, Picto) for e in entries)

    # sample: Double Third is the first row in the fixture
    double_third = next(e for e in entries if e.slug == "double-third")
    assert double_third.name == "Double Third"
    assert "double damage" in double_third.effect.lower()
    assert double_third.lumina_points_cost == 10
    assert set(double_third.stats_granted) == {"Health", "Speed", "Critical Rate"}
    assert len(double_third.sources) >= 1


def test_picto_parser_cleans_new_marker(fextralife_fixture) -> None:  # type: ignore[no-untyped-def]
    """Names flagged with 'NEW !' in Fextralife should slug cleanly."""
    page = fextralife_fixture("index_pictos")
    entries = list(parse_pictos(page))
    assert all(" NEW" not in e.name for e in entries)
    assert all("--" not in e.slug for e in entries)


def test_lumina_parser_links_source_picto(fextralife_fixture) -> None:  # type: ignore[no-untyped-def]
    page = fextralife_fixture("index_luminas")
    entries = list(parse_luminas(page))
    assert len(entries) > 150
    assert all(isinstance(e, Lumina) for e in entries)
    # each lumina must point back at the picto it comes from
    assert all(e.source_picto == e.slug for e in entries)


def test_skill_parser_extracts_character_and_cost(fextralife_fixture) -> None:  # type: ignore[no-untyped-def]
    page = fextralife_fixture("index_skills")
    entries = list(parse_skills(page))
    assert len(entries) > 100
    assert all(isinstance(e, Skill) for e in entries)
    from_fire = next(e for e in entries if e.slug == "from-fire")
    assert from_fire.ap_cost == 4
    assert from_fire.character == "Gustave"
    assert "medium single target damage" in from_fire.body.lower()


def test_weapon_parser_finds_multiple_characters(fextralife_fixture) -> None:  # type: ignore[no-untyped-def]
    page = fextralife_fixture("index_weapons")
    entries = list(parse_weapons(page))
    assert len(entries) > 50
    assert all(isinstance(e, Weapon) for e in entries)
    # weapons span multiple characters in the index
    characters = {e.character for e in entries if e.character}
    assert len(characters) >= 3


def test_character_parser_yields_six_playables(fextralife_fixture) -> None:  # type: ignore[no-untyped-def]
    page = fextralife_fixture("index_characters")
    entries = list(parse_characters(page))
    names = {e.name for e in entries}
    assert names == {"Gustave", "Lune", "Maelle", "Sciel", "Monoco", "Verso"}
    assert all(isinstance(e, Character) for e in entries)
    # Gustave's starting skills should be extracted from the bullet list
    gustave = next(e for e in entries if e.slug == "gustave")
    assert "Lumiere Assault" in gustave.signature_skills
