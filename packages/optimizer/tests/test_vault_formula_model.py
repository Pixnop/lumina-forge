"""VaultFormulaModel is the vault-driven flavour of DefaultDamageModel.

When the vault's damage-formula.md mirrors the Python defaults (which it
should, by construction), the two models must emit bit-identical output.
"""

from __future__ import annotations

from optimizer.formulas import (
    AGILITY_CRIT_RATE,
    BASE_CRIT_DAMAGE,
    LUCK_CRIT_RATE,
    MIGHT_PER_POINT,
    ROTATION_TURNS,
    DefaultDamageModel,
    VaultFormulaModel,
)
from optimizer.models import (
    Attributes,
    Build,
    CharacterItem,
    FormulaItem,
    PictoItem,
    WeaponItem,
)


def _sample_build() -> Build:
    return Build(
        character=CharacterItem(slug="x", name="X"),
        weapon=WeaponItem(slug="w", name="W", base_damage=100),
        pictos=(
            PictoItem(
                slug="a", name="A", effect="damage up",
                effect_structured={"damage_bonus": 0.2},
            ),
            PictoItem(
                slug="b", name="B", effect="crit",
                effect_structured={"crit_damage_bonus": 0.3},
            ),
            PictoItem(slug="c", name="C", effect="neutral"),
        ),
        luminas=[],
        skills_used=[],
        attributes=Attributes(might=40, agility=20, defense=10, luck=15, vitality=10),
    )


def test_vault_model_matches_defaults_when_constants_mirror_python() -> None:
    formula = FormulaItem(
        slug="damage-formula",
        name="Core damage",
        effect_structured={
            "rotation_turns": ROTATION_TURNS,
            "might_per_point": MIGHT_PER_POINT,
            "agility_crit_rate": AGILITY_CRIT_RATE,
            "luck_crit_rate": LUCK_CRIT_RATE,
            "base_crit_damage": BASE_CRIT_DAMAGE,
        },
    )
    build = _sample_build()

    default = DefaultDamageModel().estimate(build)
    vault = VaultFormulaModel.from_formula(formula).estimate(build)

    fields = (
        "base", "might_mult", "picto_mult", "lumina_mult",
        "crit_mult", "synergy_mult", "est_dps",
    )
    for name in fields:
        assert getattr(default, name) == getattr(vault, name), f"field {name} diverges"


def test_vault_model_overrides_constants() -> None:
    formula = FormulaItem(
        slug="damage-formula",
        name="Core damage (boosted)",
        effect_structured={
            "might_per_point": 0.05,  # +5% per Might instead of +2%
            "base_crit_damage": 2.0,  # 2× crit instead of 1.5×
        },
    )
    build = _sample_build()
    vault = VaultFormulaModel.from_formula(formula).estimate(build)

    # +5% × 40 might = +200% → 3× multiplier
    assert abs(vault.might_mult - 3.0) < 1e-9


def test_vault_model_falls_back_when_formula_missing() -> None:
    default = DefaultDamageModel().estimate(_sample_build())
    vault = VaultFormulaModel.from_formula(None).estimate(_sample_build())
    assert default.est_dps == vault.est_dps


def test_vault_model_applies_synergy_multiplier() -> None:
    formula = FormulaItem(slug="damage-formula", name="x", effect_structured={})
    plain = VaultFormulaModel.from_formula(formula, synergy_multiplier=1.0)
    boosted = VaultFormulaModel.from_formula(formula, synergy_multiplier=1.35)
    without = plain.estimate(_sample_build())
    withbonus = boosted.estimate(_sample_build())
    assert abs(withbonus.est_dps - without.est_dps * 1.35) < 1e-6
