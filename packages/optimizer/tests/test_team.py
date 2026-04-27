"""Team optimize: per-character builds with disjoint pictos."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from optimizer.engine import EngineOptions
from optimizer.models import Inventory
from optimizer.team import optimize_team
from optimizer.vault import VaultLoader


def test_party_of_two_picks_disjoint_pictos(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    """The mini-vault only has one character, but team optimize still has
    to enforce picto disjointness when both members draw from the same
    inventory."""
    inv = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    result = optimize_team([inv, inv], index, EngineOptions(top_k=3))
    assert result.teams, "expected at least one valid team"
    for team in result.teams:
        seen_pictos: set[str] = set()
        for member in team.members:
            picto_slugs = {p.slug for p in member.build.build.pictos}
            assert seen_pictos.isdisjoint(picto_slugs), (
                "picto must not appear on two team members"
            )
            seen_pictos.update(picto_slugs)


def test_team_score_is_sum_of_member_scores(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inv = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    result = optimize_team([inv, inv], index, EngineOptions(top_k=1))
    assert result.teams
    team = result.teams[0]
    expected = sum(m.build.total_score for m in team.members)
    assert team.total_score == pytest.approx(expected)


def test_lumina_pool_is_shared_across_team(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    """A picto mastered on one inventory should be visible as a lumina
    candidate to the other member, not just to its owner."""
    base = Inventory.model_validate(sample_inventory_dict)
    # Member A masters glass-cannon; member B doesn't have it mastered.
    a_dict = dict(sample_inventory_dict)
    a_dict["pictos_mastered"] = ["glass-cannon"]
    a = Inventory.model_validate(a_dict)
    b = base
    index = VaultLoader(mini_vault).load()
    result = optimize_team([a, b], index, EngineOptions(top_k=5))
    # We can't assert that B equips the glass-cannon lumina specifically
    # (the scorer may pick a higher-value one), but with a non-zero PP
    # budget and the shared pool, B should now be able to slot some
    # lumina that wasn't in their own inventory.
    assert result.teams
    b_member = result.teams[0].members[1]
    # PP budget=16 with shared luminas → expect at least one lumina slotted.
    assert any(
        lu.slug in {"glass-cannon", "augmented-critical", "powerful-attack"}
        for lu in b_member.build.build.luminas
    )


def test_too_few_members_rejected(
    mini_vault: Path, sample_inventory_dict: dict[str, Any]
) -> None:
    inv = Inventory.model_validate(sample_inventory_dict)
    index = VaultLoader(mini_vault).load()
    with pytest.raises(ValueError):
        optimize_team([inv], index, EngineOptions(top_k=3))
