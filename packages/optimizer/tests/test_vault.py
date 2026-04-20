"""VaultLoader reads markdown + YAML into typed indices."""

from __future__ import annotations

from pathlib import Path

from optimizer.vault import VaultLoader


def test_loader_discovers_every_type(mini_vault: Path) -> None:
    index = VaultLoader(mini_vault).load()
    assert set(index.characters) == {"gustave"}
    assert len(index.pictos) == 6
    assert len(index.weapons) == 2
    assert len(index.luminas) == 4
    assert len(index.skills) == 3
    assert index.synergies == []


def test_loader_skips_readmes_and_overview(mini_vault: Path, tmp_path: Path) -> None:
    (mini_vault / "Pictos" / "_README.md").write_text("---\nname: skip\n---\n", encoding="utf-8")
    (mini_vault / "00_Overview.md").write_text("---\nname: overview\n---\n", encoding="utf-8")

    index = VaultLoader(mini_vault).load()
    assert "_README" not in index.pictos
    assert "overview" not in index.pictos


def test_weapons_for_filters_by_character(mini_vault: Path) -> None:
    index = VaultLoader(mini_vault).load()
    gustave = {w.slug for w in index.weapons_for("gustave")}
    assert gustave == {"noahram", "heavy-hammer"}
    assert index.weapons_for("lune") == []


def test_picto_effect_structured_is_parsed(mini_vault: Path) -> None:
    index = VaultLoader(mini_vault).load()
    ac = index.pictos["augmented-critical"]
    assert ac.effect_structured == {"crit_damage_bonus": 0.30}
    assert ac.lumina_points_cost == 6
