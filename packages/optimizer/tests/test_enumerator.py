"""Enumerator honours constraints: 3 pictos, PP budget, character-compatible weapons."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pytest
from optimizer.enumerator import build_context, enumerate_builds
from optimizer.models import Inventory
from optimizer.vault import VaultLoader


def test_enumerates_expected_count(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    ctx = build_context(inventory, index)

    builds = list(enumerate_builds(ctx))
    # 2 weapons × C(6, 3) = 2 × 20 = 40
    assert len(builds) == 2 * math.comb(6, 3)


def test_every_build_has_three_unique_pictos(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    ctx = build_context(inventory, index)

    for build in enumerate_builds(ctx):
        slugs = [p.slug for p in build.pictos]
        assert len(slugs) == 3
        assert len(set(slugs)) == 3


def test_luminas_fit_pp_budget(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    ctx = build_context(inventory, index)

    for build in enumerate_builds(ctx):
        total_pp = sum(lu.pp_cost or 0 for lu in build.luminas)
        assert total_pp <= inventory.pp_budget


def test_luminas_drawn_from_mastered_and_extra(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    """Only the mastered pictos (+ luminas_extra) should contribute to the
    lumina pool, matching the in-game mastery mechanic."""
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    ctx = build_context(inventory, index)

    allowed = {"augmented-critical", "powerful-attack"}
    for build in enumerate_builds(ctx):
        for lumina in build.luminas:
            assert lumina.slug in allowed


def test_weapons_filtered_by_character(mini_vault: Path) -> None:
    # Build an inventory that asks for a weapon that doesn't belong to Gustave.
    inventory = Inventory.model_validate(
        {
            "character": "gustave",
            "weapons_available": ["noahram", "nonexistent"],
            "pictos_available": [
                "augmented-critical",
                "double-third",
                "powerful-attack",
                "glass-cannon",
            ],
            "skills_known": [],
            "pp_budget": 0,
        }
    )
    index = VaultLoader(mini_vault).load()
    ctx = build_context(inventory, index)

    assert {w.slug for w in ctx.weapons} == {"noahram"}  # unknown slug silently dropped


def test_empty_pictos_yields_no_builds(mini_vault: Path) -> None:
    inventory = Inventory.model_validate(
        {
            "character": "gustave",
            "weapons_available": ["noahram"],
            "pictos_available": [],
            "skills_known": [],
            "pp_budget": 0,
        }
    )
    index = VaultLoader(mini_vault).load()
    ctx = build_context(inventory, index)
    assert list(enumerate_builds(ctx)) == []


def test_unknown_character_raises(mini_vault: Path) -> None:
    inventory = Inventory.model_validate(
        {
            "character": "nobody",
            "weapons_available": ["noahram"],
            "pictos_available": ["augmented-critical"],
            "skills_known": [],
            "pp_budget": 0,
        }
    )
    index = VaultLoader(mini_vault).load()
    with pytest.raises(ValueError, match="nobody"):
        build_context(inventory, index)
