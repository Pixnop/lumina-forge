"""Engine: glue between inventory, enumerator, scorer and top-K ranking."""

from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass

from optimizer.enumerator import build_context, enumerate_builds
from optimizer.formulas import DamageModel, DefaultDamageModel, VaultFormulaModel
from optimizer.models import (
    Build,
    DamageEstimate,
    Inventory,
    Mode,
    RankedBuild,
    SynergyItem,
    UtilityScore,
)
from optimizer.rotation import suggest as suggest_rotation
from optimizer.synergies import SynergyMatcher
from optimizer.utility import UtilityScorer
from optimizer.vault import VaultIndex

log = logging.getLogger(__name__)


@dataclass(slots=True)
class EngineOptions:
    top_k: int = 5
    mode: Mode = "dps"
    weight_utility: float | None = None  # explicit override; else derived from mode

    def resolved_utility_weight(self) -> float:
        if self.weight_utility is not None:
            return self.weight_utility
        return {"dps": 0.0, "balanced": 0.2, "utility": 0.5}[self.mode]


def optimize(
    inventory: Inventory,
    index: VaultIndex,
    options: EngineOptions | None = None,
    *,
    damage_model: DamageModel | None = None,
) -> list[RankedBuild]:
    """Enumerate valid builds for ``inventory`` and return the top ``options.top_k``."""
    opts = options or EngineOptions()
    utility_weight = opts.resolved_utility_weight()

    # Prefer the vault-driven model when Formulas/damage-formula.md exists,
    # so editing that note changes the math without touching Python.
    if damage_model is not None:
        model: DamageModel = damage_model
    elif (formula := index.formulas.get("damage-formula")) is not None:
        model = VaultFormulaModel.from_formula(formula)
    else:
        model = DefaultDamageModel()
    matcher = SynergyMatcher(tuple(index.synergies))
    util_scorer = UtilityScorer()

    ctx = build_context(inventory, index)

    # Heap of (total_score, counter, RankedBuild). The counter disambiguates
    # equal scores so heapq never needs to compare RankedBuild objects.
    heap: list[tuple[float, int, RankedBuild]] = []
    counter = 0
    for candidate in enumerate_builds(ctx):
        ranked = _score(candidate, model, matcher, util_scorer, utility_weight)
        counter += 1
        if len(heap) < opts.top_k:
            heapq.heappush(heap, (ranked.total_score, counter, ranked))
            continue
        worst_score = heap[0][0]
        if ranked.total_score > worst_score:
            heapq.heappushpop(heap, (ranked.total_score, counter, ranked))

    heap.sort(key=lambda triple: triple[0], reverse=True)
    return [ranked for _, _, ranked in heap]


# --- internals --------------------------------------------------------------


def _score(
    build: Build,
    model: DamageModel,
    matcher: SynergyMatcher,
    util_scorer: UtilityScorer,
    utility_weight: float,
) -> RankedBuild:
    matched = matcher.matches(build)
    synergy_mult = matcher.multiplier(matched)
    damage = _apply_synergy(model.estimate(build), synergy_mult)
    damage = _apply_ceiling(damage, _build_ceiling(build, model))
    utility = util_scorer.score(build)
    total = damage.est_dps * (1.0 + utility_weight * utility.score_0_1)
    return RankedBuild(
        build=build,
        damage=damage,
        utility=utility,
        synergies_matched=matched,
        total_score=total,
        rotation_hint=suggest_rotation(build),
        why=_explain(build, damage, utility, matched),
    )


def _build_ceiling(build: Build, model: DamageModel) -> float:
    """Use the real hit counts of the build's skills when they're known.

    A 3-turn rotation that fires skills with 4-hit / 5-hit / 3-hit profiles
    can legitimately output more total damage than the conservative 3-hit
    baseline, because each hit is capped at 9999 independently. We take
    the top-3 skills by hits, sum them, and only fall back to the model's
    default ceiling when nothing's known.
    """
    ceiling = model.rotation_ceiling()
    default_rotation_turns = 3
    hit_counts = sorted(
        (s.hits for s in build.skills_used if s.hits and s.hits > 0),
        reverse=True,
    )[:default_rotation_turns]
    if not hit_counts:
        return ceiling
    cap_per_hit = ceiling / default_rotation_turns
    return cap_per_hit * sum(hit_counts)


def _apply_ceiling(damage: DamageEstimate, ceiling: float) -> DamageEstimate:
    """Clamp the final est_dps to the model's rotation ceiling (in-game cap)."""
    if damage.est_dps <= ceiling:
        return damage
    return DamageEstimate(
        base=damage.base,
        might_mult=damage.might_mult,
        picto_mult=damage.picto_mult,
        lumina_mult=damage.lumina_mult,
        crit_mult=damage.crit_mult,
        synergy_mult=damage.synergy_mult,
        est_dps=ceiling,
    )


def _apply_synergy(damage: DamageEstimate, multiplier: float) -> DamageEstimate:
    if multiplier == 1.0:
        return damage
    return DamageEstimate(
        base=damage.base,
        might_mult=damage.might_mult,
        picto_mult=damage.picto_mult,
        lumina_mult=damage.lumina_mult,
        crit_mult=damage.crit_mult,
        synergy_mult=multiplier,
        est_dps=damage.est_dps / damage.synergy_mult * multiplier,
    )


def _explain(
    build: Build,
    damage: DamageEstimate,
    utility: UtilityScore,
    matched_synergies: list[SynergyItem],
) -> list[str]:
    reasons: list[str] = [
        f"Weapon {build.weapon.name} contributes base damage {damage.base:.0f} over 3 turns.",
        f"Pictos multiplier: ×{damage.picto_mult:.2f} ({', '.join(p.name for p in build.pictos)}).",
    ]
    if build.luminas:
        reasons.append(
            f"Luminas multiplier: ×{damage.lumina_mult:.2f} "
            f"({', '.join(lu.name for lu in build.luminas)})."
        )
    reasons.append(f"Crit multiplier: ×{damage.crit_mult:.2f} (Agility + Luck).")
    if matched_synergies:
        reasons.append(
            f"Synergy bonus ×{damage.synergy_mult:.2f} from: "
            f"{', '.join(s.name for s in matched_synergies)}."
        )
    if utility.score_0_1 > 0:
        bits = []
        if utility.has_revive:
            bits.append("revive")
        if utility.has_heal:
            bits.append("heal")
        if utility.has_defense_buff:
            bits.append("defense")
        reasons.append(f"Utility: {', '.join(bits)} (score {utility.score_0_1:.2f}).")
    return reasons
