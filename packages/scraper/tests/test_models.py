"""Models must serialise sanely for the merger."""

from __future__ import annotations

from scraper.models import Lumina, Picto, Skill


def test_picto_frontmatter_omits_empty() -> None:
    picto = Picto(
        slug="augmented-critical",
        name="Augmented Critical",
        effect="+30% critical damage",
    )
    fm = picto.frontmatter()
    assert fm["type"] == "picto"
    assert fm["name"] == "Augmented Critical"
    assert fm["effect"] == "+30% critical damage"
    # empty/None fields shouldn't end up in the YAML
    assert "tier" not in fm
    assert "source_locations" not in fm
    assert "effect_structured" not in fm


def test_picto_frontmatter_preserves_zero_values() -> None:
    """A Picto that grants known stats should emit them even when magnitudes are 0."""
    picto = Picto(
        slug="fleet-foot",
        name="Fleet Foot",
        stats_granted={"Speed": 0, "Agility": 0},
    )
    fm = picto.frontmatter()
    assert fm["stats_granted"] == {"Speed": 0, "Agility": 0}


def test_lumina_source_picto_link() -> None:
    lumina = Lumina(
        slug="second-chance",
        name="Second Chance",
        pp_cost=8,
        source_picto="second-chance",
    )
    assert lumina.folder == "Luminas"
    fm = lumina.frontmatter()
    assert fm["source_picto"] == "second-chance"
    assert fm["pp_cost"] == 8


def test_skill_body_is_separate_from_frontmatter() -> None:
    skill = Skill(
        slug="powerful-strike",
        name="Powerful Strike",
        ap_cost=2,
        body="**Effect**\n\nStrikes hard.",
    )
    fm = skill.frontmatter()
    assert "body" not in fm
    assert "slug" not in fm
