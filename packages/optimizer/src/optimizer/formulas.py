"""Damage estimation.

Phase 3 uses a deliberately-simple placeholder formula behind a
``DamageModel`` Protocol. When Maxroll/Game8 adapters populate the vault
with real formulas, swap in a ``VaultFormulaModel`` that reads the
``Formulas/`` notes at startup — the engine doesn't care.

    est_dps = base × might × picto × lumina × crit × synergy

Each factor is independent and unit-tested in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from optimizer.models import Build, DamageEstimate

# Design constants — these are the tunable knobs for the placeholder formula.
ROTATION_TURNS: int = 3
MIGHT_PER_POINT: float = 0.02  # +2% damage per Might point
AGILITY_CRIT_RATE: float = 0.004  # +0.4% crit rate per Agility point
LUCK_CRIT_RATE: float = 0.004  # +0.4% crit rate per Luck point
BASE_CRIT_DAMAGE: float = 1.5
DEFAULT_PICTO_BOOST: float = 0.05  # fallback when effect_structured has nothing


class DamageModel(Protocol):
    """Contract for anything that turns a :class:`Build` into a DPS estimate."""

    def estimate(self, build: Build) -> DamageEstimate: ...


@dataclass(frozen=True, slots=True)
class DefaultDamageModel:
    """Placeholder formula — easy to reason about, trivial to unit-test."""

    synergy_multiplier: float = 1.0

    def estimate(self, build: Build) -> DamageEstimate:
        base = self._base(build)
        might_mult = self._might_mult(build)
        picto_mult = self._picto_mult(build)
        lumina_mult = self._lumina_mult(build)
        crit_mult = self._crit_mult(build)
        synergy_mult = self.synergy_multiplier
        est_dps = base * might_mult * picto_mult * lumina_mult * crit_mult * synergy_mult
        return DamageEstimate(
            base=base,
            might_mult=might_mult,
            picto_mult=picto_mult,
            lumina_mult=lumina_mult,
            crit_mult=crit_mult,
            synergy_mult=synergy_mult,
            est_dps=est_dps,
        )

    # --- factors ----------------------------------------------------------

    @staticmethod
    def _base(build: Build) -> float:
        return float(build.weapon.base_damage or 0) * ROTATION_TURNS

    @staticmethod
    def _might_mult(build: Build) -> float:
        return 1.0 + build.attributes.might * MIGHT_PER_POINT

    @staticmethod
    def _picto_mult(build: Build) -> float:
        product = 1.0
        for picto in build.pictos:
            product *= 1.0 + _picto_contribution(picto.effect_structured, picto.effect)
        return product

    @staticmethod
    def _lumina_mult(build: Build) -> float:
        total = 0.0
        for lumina in build.luminas:
            total += _picto_contribution(lumina.effect_structured, lumina.effect)
        return 1.0 + total

    @staticmethod
    def _crit_mult(build: Build) -> float:
        attrs = build.attributes
        crit_rate = min(1.0, (attrs.agility * AGILITY_CRIT_RATE) + (attrs.luck * LUCK_CRIT_RATE))
        return 1.0 + crit_rate * (BASE_CRIT_DAMAGE - 1.0)


# --- heuristics -------------------------------------------------------------


_NUMERIC_KEYS_DIRECT = frozenset(
    {
        "damage_bonus",
        "crit_damage_bonus",
        "crit_rate_bonus",
        "might_mult",
        "multiplier",
    }
)
_KEYWORDS_DPS = ("damage", "hit", "strike", "critical", "burn", "stain", "powerful")


def _picto_contribution(effect_structured: dict[str, object], effect_text: str) -> float:
    """Heuristic: if ``effect_structured`` has known DPS keys, use them;
    otherwise nudge the multiplier up slightly when the effect description
    reads offensive. Clamp to a reasonable range to prevent runaway stacks."""
    numeric_sum = 0.0
    for key, value in effect_structured.items():
        if not isinstance(value, int | float):
            continue
        if key in _NUMERIC_KEYS_DIRECT or "damage" in key or "crit" in key:
            numeric_sum += float(value)
    if numeric_sum > 0:
        return min(numeric_sum, 1.0)
    low = (effect_text or "").lower()
    return DEFAULT_PICTO_BOOST if any(word in low for word in _KEYWORDS_DPS) else 0.0
