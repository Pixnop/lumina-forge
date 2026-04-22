"""DefaultDamageModel must be deterministic and factor-wise predictable."""

from __future__ import annotations

from optimizer.formulas import DefaultDamageModel
from optimizer.models import Attributes, Build, CharacterItem, PictoItem, WeaponItem


def _build(**overrides) -> Build:  # type: ignore[no-untyped-def]
    character = CharacterItem(slug="x", name="X", role="Offensive")
    weapon = WeaponItem(slug="w", name="W", base_damage=100, scaling_stat="Might")
    neutral_picto = PictoItem(slug="p", name="P", effect="neutral")
    pictos = (neutral_picto, neutral_picto, neutral_picto)
    base = Build(
        character=character,
        weapon=weapon,
        pictos=pictos,
        luminas=[],
        skills_used=[],
        attributes=Attributes(),
    )
    return base.model_copy(update=overrides)


def test_base_factor_scales_with_weapon_damage() -> None:
    b = _build()
    est = DefaultDamageModel().estimate(b)
    # 100 base_damage * 3 rotation turns = 300
    assert est.base == 300.0


def test_might_mult_is_linear() -> None:
    b = _build(attributes=Attributes(might=50))
    est = DefaultDamageModel().estimate(b)
    assert est.might_mult == 1.0 + 50 * 0.02  # = 2.0


def test_picto_mult_uses_effect_structured() -> None:
    damage_picto = PictoItem(
        slug="d",
        name="D",
        effect="damage up",
        effect_structured={"damage_bonus": 0.2},
    )
    b = _build(pictos=(damage_picto, damage_picto, damage_picto))
    est = DefaultDamageModel().estimate(b)
    assert abs(est.picto_mult - 1.2 ** 3) < 1e-9


def test_crit_mult_combines_agility_and_luck() -> None:
    b = _build(attributes=Attributes(agility=50, luck=50))
    est = DefaultDamageModel().estimate(b)
    crit_rate = 50 * 0.004 + 50 * 0.004  # = 0.4
    expected = 1.0 + crit_rate * (1.5 - 1.0)  # = 1.2
    assert abs(est.crit_mult - expected) < 1e-9


def test_full_formula_is_product_of_factors() -> None:
    damage_picto = PictoItem(
        slug="d", name="D", effect="damage", effect_structured={"damage_bonus": 0.2}
    )
    b = _build(
        attributes=Attributes(might=10, agility=25, luck=25),
        pictos=(damage_picto, damage_picto, damage_picto),
    )
    est = DefaultDamageModel().estimate(b)
    expected = (
        est.base
        * est.might_mult
        * est.picto_mult
        * est.lumina_mult
        * est.crit_mult
        * est.synergy_mult
        * est.ap_mult
    )
    assert abs(est.est_dps - expected) < 1e-6


def test_zero_damage_weapon_returns_zero_dps() -> None:
    b = _build(weapon=WeaponItem(slug="w", name="W", base_damage=0))
    est = DefaultDamageModel().estimate(b)
    assert est.base == 0.0
    assert est.est_dps == 0.0


# --- AP economy -------------------------------------------------------------


def test_ap_mult_is_one_without_ap_pictos() -> None:
    b = _build()
    est = DefaultDamageModel().estimate(b)
    assert est.ap_mult == 1.0


def test_ap_mult_rises_with_turn_start_ap() -> None:
    """+1 AP on turn start fires every turn — 3 AP/rotation across 3 turns."""
    ap_picto = PictoItem(
        slug="energising-turn",
        name="E",
        effect="+1 AP on turn start.",
        effect_structured={"ap_bonus": 1, "ap_trigger": "turn_start"},
    )
    b = _build(pictos=(ap_picto, ap_picto, ap_picto))
    est = DefaultDamageModel().estimate(b)
    assert est.ap_mult > 1.0


def test_ap_mult_ignores_non_ap_fields() -> None:
    damage_picto = PictoItem(
        slug="d", name="D", effect="dmg", effect_structured={"damage_bonus": 0.5}
    )
    b = _build(pictos=(damage_picto, damage_picto, damage_picto))
    est = DefaultDamageModel().estimate(b)
    assert est.ap_mult == 1.0  # no ap_bonus on these pictos


def test_ap_mult_is_capped() -> None:
    """Stacking every AP picto in the vault shouldn't send ap_mult to 10×."""
    huge_ap = PictoItem(
        slug="huge",
        name="H",
        effect="+100 AP on turn start.",
        effect_structured={"ap_bonus": 100, "ap_trigger": "turn_start"},
    )
    b = _build(pictos=(huge_ap, huge_ap, huge_ap))
    est = DefaultDamageModel().estimate(b)
    assert est.ap_mult <= 1.50  # the explicit cap
