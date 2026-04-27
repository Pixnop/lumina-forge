"""Test fixtures for the optimizer suite.

We build a mini-vault on ``tmp_path`` rather than committing hundreds of
tiny markdown files. The mini-vault covers every entry type with a handful
of entries, enough for deterministic unit tests of the loader, enumerator,
scorer and end-to-end engine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from optimizer.formulas import clear_caches as _clear_formula_caches


@pytest.fixture(autouse=True)
def _reset_formula_caches() -> None:
    """Wipe the _picto_contribution cache between tests — it's content-keyed,
    so it's safe across runs, but a fresh slate keeps perf assertions and
    timing-sensitive tests honest."""
    _clear_formula_caches()


def _write(
    vault: Path, folder: str, slug: str, frontmatter: dict[str, Any], body: str = ""
) -> None:
    folder_path = vault / folder
    folder_path.mkdir(parents=True, exist_ok=True)
    yaml_text = yaml.safe_dump(frontmatter, sort_keys=True, allow_unicode=True)
    (folder_path / f"{slug}.md").write_text(
        f"---\n{yaml_text}---\n\n{body}\n",
        encoding="utf-8",
    )


@pytest.fixture
def mini_vault(tmp_path: Path) -> Path:
    """Build a minimal but realistic vault for optimizer tests."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # --- one character ------------------------------------------------------
    _write(
        vault,
        "Characters",
        "gustave",
        {
            "type": "character",
            "name": "Gustave",
            "role": "Offensive",
            "primary_stat": "Might",
            "signature_skills": ["lumiere-assault", "overcharge"],
            "archetypes": ["Overcharge"],
        },
        "Gustave opens strong, builds gradient, finishes with Overcharge.",
    )

    # --- two weapons (both Gustave-compatible) -----------------------------
    _write(
        vault,
        "Weapons",
        "noahram",
        {
            "type": "weapon",
            "name": "Noahram",
            "character": "Gustave",
            "base_damage": 100,
            "scaling_stat": "Might",
            "passives": [],
        },
    )
    _write(
        vault,
        "Weapons",
        "heavy-hammer",
        {
            "type": "weapon",
            "name": "Heavy Hammer",
            "character": "Gustave",
            "base_damage": 150,
            "scaling_stat": "Might",
            "passives": [],
        },
    )

    # --- six pictos (4 offensive, 2 defensive) -----------------------------
    _write(
        vault,
        "Pictos",
        "augmented-critical",
        {
            "type": "picto",
            "name": "Augmented Critical",
            "category": "Offensive",
            "effect": "+30% critical damage",
            "effect_structured": {"crit_damage_bonus": 0.30},
            "stats_granted": {"Might": 8, "Luck": 4},
            "lumina_points_cost": 6,
        },
    )
    _write(
        vault,
        "Pictos",
        "double-third",
        {
            "type": "picto",
            "name": "Double Third",
            "category": "Offensive",
            "effect": "Every third hit of a Skill deals double damage.",
            "effect_structured": {"damage_bonus": 0.15},
            "stats_granted": {"Speed": 0},
            "lumina_points_cost": 10,
        },
    )
    _write(
        vault,
        "Pictos",
        "powerful-attack",
        {
            "type": "picto",
            "name": "Powerful Attack",
            "category": "Offensive",
            "effect": "Increases damage of Powerful skills.",
            "effect_structured": {"damage_bonus": 0.10},
            "stats_granted": {"Might": 6},
            "lumina_points_cost": 4,
        },
    )
    _write(
        vault,
        "Pictos",
        "glass-cannon",
        {
            "type": "picto",
            "name": "Glass Cannon",
            "category": "Offensive",
            "effect": "Double damage, halved health.",
            "effect_structured": {"damage_bonus": 0.5},
            "stats_granted": {"Might": 12},
            "lumina_points_cost": 8,
        },
    )
    _write(
        vault,
        "Pictos",
        "second-chance",
        {
            "type": "picto",
            "name": "Second Chance",
            "category": "Defensive",
            "effect": "Revive with 50% HP once per battle.",
            "effect_structured": {},
            "stats_granted": {"Health": 0},
            "lumina_points_cost": 8,
        },
    )
    _write(
        vault,
        "Pictos",
        "accelerating-heal",
        {
            "type": "picto",
            "name": "Accelerating Heal",
            "category": "Defensive",
            "effect": "Healing effects restore more HP.",
            "effect_structured": {},
            "stats_granted": {"Health": 0},
            "lumina_points_cost": 3,
        },
    )

    # --- four luminas mirroring four pictos --------------------------------
    for slug, name, cost, effect in [
        ("augmented-critical", "Augmented Critical", 6, "+30% critical damage"),
        ("powerful-attack", "Powerful Attack", 4, "Increases damage of Powerful skills."),
        ("glass-cannon", "Glass Cannon", 8, "Double damage, halved health."),
        ("second-chance", "Second Chance", 8, "Revive with 50% HP once per battle."),
    ]:
        _write(
            vault,
            "Luminas",
            slug,
            {
                "type": "lumina",
                "name": name,
                "pp_cost": cost,
                "effect": effect,
                "source_picto": slug,
                "effect_structured": (
                    {"damage_bonus": 0.2} if "damage" in effect.lower() else {}
                ),
            },
        )

    # --- three skills ------------------------------------------------------
    _write(
        vault,
        "Skills",
        "lumiere-assault",
        {
            "type": "skill",
            "name": "Lumiere Assault",
            "character": "Gustave",
            "ap_cost": 2,
            "category": "Offensive",
        },
        "**Effect**\n\nStrikes a single enemy for heavy damage.",
    )
    _write(
        vault,
        "Skills",
        "overcharge",
        {
            "type": "skill",
            "name": "Overcharge",
            "character": "Gustave",
            "ap_cost": 3,
            "category": "Buff",
        },
        "**Effect**\n\nPrepare a devastating burst for the next turn.",
    )
    _write(
        vault,
        "Skills",
        "finisher-strike",
        {
            "type": "skill",
            "name": "Finisher Strike",
            "character": "Gustave",
            "ap_cost": 4,
            "category": "Offensive",
        },
        "**Effect**\n\nExecutes low-HP enemies for massive bonus damage.",
    )

    # --- no synergies yet — folder stays empty -----------------------------
    return vault


@pytest.fixture
def sample_inventory_dict() -> dict[str, Any]:
    return {
        "character": "gustave",
        "level": 10,
        "attributes": {
            "might": 20,
            "agility": 10,
            "defense": 5,
            "luck": 5,
            "vitality": 5,
        },
        "weapons_available": ["noahram", "heavy-hammer"],
        "pictos_available": [
            "augmented-critical",
            "double-third",
            "powerful-attack",
            "glass-cannon",
            "second-chance",
            "accelerating-heal",
        ],
        "pictos_mastered": ["augmented-critical", "powerful-attack"],
        "luminas_extra": [],
        "pp_budget": 16,
        "skills_known": ["lumiere-assault", "overcharge", "finisher-strike"],
    }
