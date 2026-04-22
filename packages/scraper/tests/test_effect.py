"""Unit tests for the structured-effect parser.

Each case doubles as a living spec — when the optimizer reads
``effect_structured`` it's these fields it multiplies onto damage.
"""

from __future__ import annotations

import pytest
from scraper.sources.fextralife.parsers._effect import parse_effect_structured

# --- existing patterns (regression guard) -----------------------------------


class TestExistingPatterns:
    def test_flat_damage_percent(self) -> None:
        assert parse_effect_structured("50% increased Base Attack damage") == {
            "damage_bonus": 0.5
        }

    def test_crit_damage(self) -> None:
        assert parse_effect_structured("25% increased Critical Damage") == {
            "crit_damage_bonus": 0.25
        }

    def test_crit_rate_conditional(self) -> None:
        result = parse_effect_structured("25% increased Critical Chance on Burning enemies")
        assert result["crit_rate_bonus"] == 0.25

    def test_every_third_hit(self) -> None:
        result = parse_effect_structured("Every third hit of a Skill deals double damage.")
        assert result["damage_bonus"] == 0.33

    def test_revive_flag(self) -> None:
        assert parse_effect_structured("Revive with 50% HP once per battle")["has_revive"] is True

    def test_empty_text(self) -> None:
        assert parse_effect_structured("") == {}

    def test_immunity_yields_no_damage_bonus(self) -> None:
        """Status immunities don't affect damage output. An ``immunity``
        field is populated (v0.5 taxonomy) but no damage_bonus."""
        result = parse_effect_structured("Immune to Burn.")
        assert "damage_bonus" not in result


# --- new patterns for v0.5.0 ------------------------------------------------


class TestHiddenDamageMultiplier:
    """Pictos like ``first-strike`` and ``dead-energy-ii`` carry a hidden
    flat damage buff expressed as ``1.1x damage``. Convert to a fraction."""

    def test_first_strike(self) -> None:
        result = parse_effect_structured(
            "Play first (Also gives a hidden 1.1x damage buff when equipped)."
        )
        assert result.get("damage_bonus") == pytest.approx(0.10)

    def test_dead_energy_ii(self) -> None:
        result = parse_effect_structured(
            "+3 AP on killing an enemy (Also gives a hidden 1.1x damage buff when equipped)."
        )
        assert result.get("damage_bonus") == pytest.approx(0.10)

    def test_hidden_two_x_buff(self) -> None:
        result = parse_effect_structured("gives a hidden 2x damage buff when equipped")
        assert result.get("damage_bonus") == pytest.approx(1.0)


class TestDamageCapBypass:
    def test_painted_power(self) -> None:
        result = parse_effect_structured("Damage can exceed 9,999.")
        assert result.get("damage_cap_bypass") is True

    def test_no_comma_variant(self) -> None:
        result = parse_effect_structured("damage can exceed 9999")
        assert result.get("damage_cap_bypass") is True


class TestBreakSpecialist:
    """'Break damage is increased by 50%, but base damage is reduced by 20%.'"""

    def test_break_and_base_deltas(self) -> None:
        result = parse_effect_structured(
            "Break damage is increased by 50%, but base damage is reduced by 20%."
        )
        assert result.get("break_damage_bonus") == pytest.approx(0.50)
        assert result.get("damage_bonus") == pytest.approx(-0.20)

    def test_break_only(self) -> None:
        result = parse_effect_structured("Break damage is increased by 75%.")
        assert result.get("break_damage_bonus") == pytest.approx(0.75)


class TestBattleStartBuffs:
    """'Apply Powerful for N turns on battle start' — Powerful = +50% dmg."""

    def test_auto_powerful(self) -> None:
        result = parse_effect_structured("Apply Powerful for 3 turns on battle start.")
        # Powerful = +50%; 3 turns across a 3-turn rotation = ~full uptime.
        assert result.get("damage_bonus") == pytest.approx(0.50)

    def test_auto_powerful_single_turn(self) -> None:
        result = parse_effect_structured("Apply Powerful for 1 turn on battle start.")
        # 1/3 uptime
        assert result.get("damage_bonus") == pytest.approx(0.5 / 3, rel=0.05)

    def test_auto_rush_is_not_offensive(self) -> None:
        """Rush affects turn order, not damage — no damage_bonus expected."""
        result = parse_effect_structured("Apply Rush for 3 turns on battle start.")
        assert "damage_bonus" not in result

    def test_auto_shell_is_not_offensive(self) -> None:
        result = parse_effect_structured("Apply Shell for 3 turns on battle start.")
        assert "damage_bonus" not in result


class TestConditionalDamageIncrease:
    """Verb-first / verb-middle patterns the original regex missed."""

    def test_versatile_conditional(self) -> None:
        result = parse_effect_structured(
            "After a Free Aim hit, Base Attack damage is increased by 50% for 1 turn."
        )
        assert result.get("damage_bonus") == pytest.approx(0.50)
        # First-attack uptime is low — the existing uptime estimator should tag it
        assert result.get("trigger_uptime", 1.0) < 0.5

    def test_powered_attack(self) -> None:
        result = parse_effect_structured(
            "On every damage dealt, try to consume 1 AP. If successful, increase damage by 20%."
        )
        assert result.get("damage_bonus") == pytest.approx(0.20)

    def test_empowering_parry(self) -> None:
        result = parse_effect_structured(
            "Each successful Parry increases damage by 5% until end of the following turn."
        )
        assert result.get("damage_bonus") == pytest.approx(0.05)


class TestNonDamageFields:
    """Every picto/lumina should land with SOME structured data so the
    vault browser can show it — even when damage_bonus stays zero."""

    def test_ap_on_kill(self) -> None:
        result = parse_effect_structured("+3 AP on killing an enemy.")
        assert result.get("ap_bonus") == 3
        assert result.get("ap_trigger") == "on_kill"

    def test_ap_on_battle_start(self) -> None:
        result = parse_effect_structured("+1 AP on battle start.")
        assert result.get("ap_bonus") == 1
        assert result.get("ap_trigger") == "battle_start"

    def test_ap_on_parry(self) -> None:
        result = parse_effect_structured("+1 AP on successful Parry.")
        assert result.get("ap_bonus") == 1
        assert result.get("ap_trigger") == "parry"

    def test_gradient_charge_on_break(self) -> None:
        result = parse_effect_structured("+50% of a Gradient Charge on Breaking a target.")
        assert result.get("gradient_bonus") == pytest.approx(0.5)
        assert result.get("gradient_trigger") == "on_break"

    def test_gradient_charge_on_crit(self) -> None:
        result = parse_effect_structured(
            "+20% of a Gradient Charge on Critical Hit. Once per turn."
        )
        assert result.get("gradient_bonus") == pytest.approx(0.2)
        assert result.get("gradient_trigger") == "critical_hit"

    def test_immunity_burn(self) -> None:
        result = parse_effect_structured("Immune to Burn.")
        assert result.get("immunity") == "burn"

    def test_immunity_stun(self) -> None:
        result = parse_effect_structured("Immune to Stun .")
        assert result.get("immunity") == "stun"

    def test_applies_rush_on_battle_start(self) -> None:
        result = parse_effect_structured("Apply Rush for 3 turns on battle start.")
        # Rush isn't offensive — no damage_bonus — but we still want the
        # buff name captured.
        assert "damage_bonus" not in result
        assert result.get("applies_buff") == "rush"

    def test_applies_shell(self) -> None:
        result = parse_effect_structured("Apply Shell for 3 turns on battle start.")
        assert result.get("applies_buff") == "shell"

    def test_extends_burn_duration(self) -> None:
        result = parse_effect_structured("Burn duration is increased by 2.")
        assert result.get("extends_status") == "burn"
        assert result.get("extends_status_turns") == 2

    def test_extends_powerful_duration(self) -> None:
        result = parse_effect_structured(
            "On applying Powerful, its duration is increased by 2."
        )
        assert result.get("extends_status") == "powerful"
        assert result.get("extends_status_turns") == 2

    def test_extends_break_duration(self) -> None:
        result = parse_effect_structured(
            "Breaks last 1 more turn but the target can't be Broken twice."
        )
        assert result.get("extends_status") == "break"
        assert result.get("extends_status_turns") == 1
