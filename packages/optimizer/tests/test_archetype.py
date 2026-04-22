"""Archetype matcher + aspirational finder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from optimizer.archetype import ArchetypeMatcher, find_aspirational
from optimizer.engine import EngineOptions, optimize
from optimizer.models import Attributes, Build, CuratedBuild, Inventory
from optimizer.vault import VaultIndex, VaultLoader

# --- test helpers -----------------------------------------------------------


def _write_curated(vault: Path, slug: str, frontmatter: dict[str, Any]) -> None:
    folder = vault / "Builds"
    folder.mkdir(parents=True, exist_ok=True)
    yaml_text = yaml.safe_dump(frontmatter, sort_keys=True, allow_unicode=True)
    (folder / f"{slug}.md").write_text(
        f"---\n{yaml_text}---\n\nbody\n",
        encoding="utf-8",
    )


def _canonical_curated(weapon: str = "Weapons/noahram") -> dict[str, Any]:
    return {
        "type": "build",
        "name": "Gustave — Mini Overcharge",
        "character": "Gustave",
        "archetype": "Overcharge",
        "role": "Offensive",
        "dps_tier": "S",
        "weapon": weapon,
        "pictos": [
            "Pictos/augmented-critical",
            "Pictos/powerful-attack",
            "Pictos/glass-cannon",
        ],
        "luminas": [
            "Luminas/augmented-critical",
            "Luminas/powerful-attack",
        ],
        "required_skills": ["Skills/overcharge"],
    }


# --- CuratedBuild model -----------------------------------------------------


def test_curated_build_strips_folder_prefixes() -> None:
    cb = CuratedBuild.model_validate(
        {
            "slug": "test",
            "name": "Test",
            "weapon": "Weapons/noahram",
            "pictos": ["Pictos/a", "Pictos/b", "Pictos/c"],
            "luminas": ["Luminas/x"],
            "required_skills": ["Skills/overcharge"],
        }
    )
    assert cb.weapon == "noahram"
    assert cb.pictos == ["a", "b", "c"]
    assert cb.luminas == ["x"]
    assert cb.required_skills == ["overcharge"]


def test_curated_build_leaves_bare_slugs_alone() -> None:
    cb = CuratedBuild.model_validate(
        {"slug": "t", "name": "T", "weapon": "noahram", "pictos": ["a", "b", "c"]}
    )
    assert cb.weapon == "noahram"
    assert cb.pictos == ["a", "b", "c"]


# --- Vault loader with Builds/ ---------------------------------------------


def test_loader_populates_curated_builds(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    _write_curated(mini_vault, "mini-overcharge", _canonical_curated())
    index = VaultLoader(mini_vault).load()
    assert len(index.curated_builds) == 1
    assert index.curated_builds[0].slug == "mini-overcharge"
    assert index.curated_builds[0].dps_tier == "S"


# --- ArchetypeMatcher -------------------------------------------------------


def _build_from_index(index: VaultIndex, *, weapon_slug: str) -> Build:
    """Construct a Build directly — bypassing enumerator dedup so we can test
    both weapon variants of the same loadout."""
    return Build(
        character=index.characters["gustave"],
        weapon=index.weapons[weapon_slug],
        pictos=(
            index.pictos["augmented-critical"],
            index.pictos["powerful-attack"],
            index.pictos["glass-cannon"],
        ),
        luminas=[
            index.luminas["augmented-critical"],
            index.luminas["powerful-attack"],
        ],
        skills_used=list(index.skills.values()),
        attributes=Attributes(might=20, agility=10, defense=5, luck=5, vitality=5),
    )


def test_exact_match_gets_full_tier_bonus(mini_vault: Path) -> None:
    _write_curated(mini_vault, "mini-overcharge", _canonical_curated(weapon="Weapons/noahram"))
    index = VaultLoader(mini_vault).load()
    matcher = ArchetypeMatcher(tuple(index.curated_builds))
    build = _build_from_index(index, weapon_slug="noahram")

    match = matcher.match(build, skills_known=frozenset({"overcharge"}))
    assert match is not None
    assert match.confidence == "exact"
    assert match.dps_tier == "S"
    assert match.bonus_applied == 0.08


def test_variant_match_halves_the_bonus(mini_vault: Path) -> None:
    _write_curated(mini_vault, "mini-overcharge", _canonical_curated(weapon="Weapons/noahram"))
    index = VaultLoader(mini_vault).load()
    matcher = ArchetypeMatcher(tuple(index.curated_builds))
    # Same loadout but different weapon — heavy-hammer instead of noahram.
    build = _build_from_index(index, weapon_slug="heavy-hammer")

    match = matcher.match(build, skills_known=frozenset({"overcharge"}))
    assert match is not None
    assert match.confidence == "variant"
    assert match.bonus_applied == 0.04


def test_missing_required_skill_blocks_match(mini_vault: Path) -> None:
    _write_curated(mini_vault, "mini-overcharge", _canonical_curated())
    index = VaultLoader(mini_vault).load()
    matcher = ArchetypeMatcher(tuple(index.curated_builds))
    build = _build_from_index(index, weapon_slug="noahram")

    # Player doesn't know Overcharge — no match even if the items line up.
    assert matcher.match(build, skills_known=frozenset()) is None


def test_picto_mismatch_blocks_match(mini_vault: Path) -> None:
    variant = _canonical_curated()
    variant["pictos"] = [
        "Pictos/augmented-critical",
        "Pictos/powerful-attack",
        "Pictos/double-third",  # differs from the canonical _build_from_index
    ]
    _write_curated(mini_vault, "off-archetype", variant)
    index = VaultLoader(mini_vault).load()
    matcher = ArchetypeMatcher(tuple(index.curated_builds))
    build = _build_from_index(index, weapon_slug="noahram")

    # Pictos differ → not this archetype even though 2/3 overlap.
    assert matcher.match(build, skills_known=frozenset({"overcharge"})) is None


# --- Aspirational finder ----------------------------------------------------


def test_aspirational_flags_missing_skill(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    _write_curated(mini_vault, "mini-overcharge", _canonical_curated())
    index = VaultLoader(mini_vault).load()

    inv_dict = dict(sample_inventory_dict)
    inv_dict["skills_known"] = ["lumiere-assault", "finisher-strike"]  # no overcharge
    inventory = Inventory.model_validate(inv_dict)

    aspirational = find_aspirational(index.curated_builds, inventory)
    assert len(aspirational) == 1
    assert aspirational[0].missing_skills == ["overcharge"]
    assert aspirational[0].missing_count() == 1


def test_aspirational_respects_max_missing(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    # Require a weapon + two pictos + a skill the player doesn't have.
    far = _canonical_curated(weapon="Weapons/unknown-weapon")
    far["pictos"] = [
        "Pictos/unknown-picto-a",  # not in the player's pictos_available
        "Pictos/unknown-picto-b",
        "Pictos/augmented-critical",
    ]
    _write_curated(mini_vault, "far-away", far)
    index = VaultLoader(mini_vault).load()

    inv_dict = dict(sample_inventory_dict)
    inv_dict["skills_known"] = []
    inventory = Inventory.model_validate(inv_dict)

    # default max_missing=2 ⇒ this 4-missing build is skipped
    assert find_aspirational(index.curated_builds, inventory) == []
    # with max_missing=5 it shows up
    relaxed = find_aspirational(index.curated_builds, inventory, max_missing=5)
    assert len(relaxed) == 1


def test_aspirational_skips_fully_owned(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    _write_curated(mini_vault, "mini-overcharge", _canonical_curated())
    index = VaultLoader(mini_vault).load()

    # Master the third picto so the player owns everything already.
    inv_dict = dict(sample_inventory_dict)
    inv_dict["pictos_mastered"] = [
        "augmented-critical",
        "powerful-attack",
        "glass-cannon",
    ]
    inventory = Inventory.model_validate(inv_dict)

    assert find_aspirational(index.curated_builds, inventory) == []


def test_aspirational_ignores_other_characters(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    other = _canonical_curated()
    other["character"] = "Lune"
    _write_curated(mini_vault, "lune-build", other)
    index = VaultLoader(mini_vault).load()

    inv_dict = dict(sample_inventory_dict)
    inv_dict["skills_known"] = []  # would be aspirational for Gustave otherwise
    inventory = Inventory.model_validate(inv_dict)

    assert find_aspirational(index.curated_builds, inventory) == []


# --- Engine integration -----------------------------------------------------


def test_archetype_tags_a_matching_build_and_bonus_applies(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    _write_curated(mini_vault, "mini-overcharge", _canonical_curated(weapon="Weapons/heavy-hammer"))
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()

    result = optimize(inventory, index, EngineOptions(top_k=20))
    matched = [r for r in result.builds if r.archetype is not None]
    assert matched, "expected at least one build to match the archetype"
    # The exact-match build gains the full 8% bonus — total_score > est_dps
    # by the bonus fraction.
    best = matched[0]
    assert best.total_score > best.damage.est_dps * 1.05
