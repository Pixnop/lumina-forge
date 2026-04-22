"""End-to-end: JSON inventory → top 5 ranked builds."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from optimizer.engine import EngineOptions, optimize
from optimizer.models import Inventory
from optimizer.vault import VaultLoader


def test_returns_requested_top_k(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    result = optimize(inventory, index, EngineOptions(top_k=5))
    assert len(result.builds) == 5


def test_ranking_is_sorted_descending(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    result = optimize(inventory, index, EngineOptions(top_k=5))
    scores = [r.total_score for r in result.builds]
    assert scores == sorted(scores, reverse=True)


def test_best_build_prefers_stronger_weapon(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    """Heavy Hammer (150 base) beats Noahram (100 base), all else equal."""
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    result = optimize(inventory, index, EngineOptions(top_k=1))
    assert result.builds[0].build.weapon.slug == "heavy-hammer"


def test_utility_mode_bumps_defensive_builds(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    """In utility mode, defensive pictos should appear higher in the ranking."""
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    dps_top = optimize(inventory, index, EngineOptions(top_k=10, mode="dps")).builds
    util_top = optimize(inventory, index, EngineOptions(top_k=10, mode="utility")).builds

    def has_defensive(rb) -> bool:  # type: ignore[no-untyped-def]
        return any(p.category == "Defensive" for p in rb.build.pictos)

    dps_first_defensive = next((i for i, rb in enumerate(dps_top) if has_defensive(rb)), None)
    util_first_defensive = next((i for i, rb in enumerate(util_top) if has_defensive(rb)), None)
    assert dps_first_defensive is not None
    assert util_first_defensive is not None
    # Utility mode ranks the first defensive build at least as early as DPS mode.
    assert util_first_defensive <= dps_first_defensive


def test_rotation_hint_is_populated(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    result = optimize(inventory, index, EngineOptions(top_k=1))
    assert 1 <= len(result.builds[0].rotation_hint) <= 3
    assert all(isinstance(line, str) and line for line in result.builds[0].rotation_hint)


def test_why_reasons_are_non_empty(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inventory = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    result = optimize(inventory, index, EngineOptions(top_k=1))
    assert len(result.builds[0].why) >= 2
