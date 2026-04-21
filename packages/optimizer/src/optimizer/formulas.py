"""Damage estimation.

Two models implement the ``DamageModel`` protocol:

- :class:`DefaultDamageModel` hard-codes the constants (kept as a
  fallback when the vault is empty or unavailable).
- :class:`VaultFormulaModel` reads the same knobs from
  ``vault/Formulas/damage-formula.md``'s ``effect_structured`` block,
  so iterating on the math is now a data edit instead of a code change.

Both compute the same equation:

    est_dps = base × might × picto × lumina × crit × synergy
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from optimizer.models import Build, DamageEstimate, FormulaItem

# Placeholder-formula defaults. Mirrored in vault/Formulas/damage-formula.md
# so the two models produce identical numbers out of the box.
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
    """Placeholder formula with hard-coded constants."""

    synergy_multiplier: float = 1.0
    rotation_turns: int = ROTATION_TURNS
    might_per_point: float = MIGHT_PER_POINT
    agility_crit_rate: float = AGILITY_CRIT_RATE
    luck_crit_rate: float = LUCK_CRIT_RATE
    base_crit_damage: float = BASE_CRIT_DAMAGE

    def estimate(self, build: Build) -> DamageEstimate:
        base = float(build.weapon.base_damage or 0) * self.rotation_turns
        might_mult = 1.0 + build.attributes.might * self.might_per_point
        picto_mult = 1.0
        for picto in build.pictos:
            picto_mult *= 1.0 + _picto_contribution(picto.effect_structured, picto.effect)
        lumina_total = 0.0
        for lumina in build.luminas:
            lumina_total += _picto_contribution(lumina.effect_structured, lumina.effect)
        lumina_mult = 1.0 + lumina_total
        crit_rate = min(
            1.0,
            (build.attributes.agility * self.agility_crit_rate)
            + (build.attributes.luck * self.luck_crit_rate),
        )
        crit_mult = 1.0 + crit_rate * (self.base_crit_damage - 1.0)
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


@dataclass(frozen=True, slots=True)
class VaultFormulaModel:
    """A :class:`DefaultDamageModel` whose constants come from the vault.

    Use :meth:`from_formula` to pull the knobs from a ``FormulaItem`` loaded
    via ``VaultLoader`` — typically the note at ``Formulas/damage-formula.md``.
    Missing keys fall back to the Python defaults, so a partially-populated
    formula note still produces a coherent model.
    """

    inner: DefaultDamageModel

    def estimate(self, build: Build) -> DamageEstimate:
        return self.inner.estimate(build)

    @classmethod
    def from_formula(
        cls,
        formula: FormulaItem | None,
        synergy_multiplier: float = 1.0,
    ) -> VaultFormulaModel:
        if formula is None:
            return cls(inner=DefaultDamageModel(synergy_multiplier=synergy_multiplier))
        s = formula.effect_structured
        inner = DefaultDamageModel(
            synergy_multiplier=synergy_multiplier,
            rotation_turns=_as_int(s.get("rotation_turns"), ROTATION_TURNS),
            might_per_point=_as_float(s.get("might_per_point"), MIGHT_PER_POINT),
            agility_crit_rate=_as_float(s.get("agility_crit_rate"), AGILITY_CRIT_RATE),
            luck_crit_rate=_as_float(s.get("luck_crit_rate"), LUCK_CRIT_RATE),
            base_crit_damage=_as_float(s.get("base_crit_damage"), BASE_CRIT_DAMAGE),
        )
        return cls(inner=inner)


def _as_float(raw: object, default: float) -> float:
    if isinstance(raw, int | float):
        return float(raw)
    return default


def _as_int(raw: object, default: int) -> int:
    if isinstance(raw, int | float):
        return int(raw)
    return default


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
