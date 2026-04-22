"""Engine: glue between inventory, enumerator, scorer and top-K ranking."""

from __future__ import annotations

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
    WeaponAlternative,
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
    """Enumerate valid builds for ``inventory`` and return the top ``options.top_k``.

    Builds are deduplicated by their (pictos, luminas) signature — for
    each distinct combo, the best-scoring weapon wins and the runners-up
    land in ``RankedBuild.weapon_alternatives``. This stops the top-K
    from being five copies of the same loadout with only the weapon slot
    changing.
    """
    opts = options or EngineOptions()
    utility_weight = opts.resolved_utility_weight()

    # Prefer the vault-driven model when Formulas/damage-formula.md exists.
    if damage_model is not None:
        model: DamageModel = damage_model
    elif (formula := index.formulas.get("damage-formula")) is not None:
        model = VaultFormulaModel.from_formula(formula)
    else:
        model = DefaultDamageModel()
    matcher = SynergyMatcher(tuple(index.synergies))
    util_scorer = UtilityScorer()

    ctx = build_context(inventory, index)

    # Stage 1 — score every candidate and bucket them by loadout signature.
    groups: dict[tuple[str, ...], list[RankedBuild]] = {}
    for candidate in enumerate_builds(ctx):
        ranked = _score(candidate, model, matcher, util_scorer, utility_weight)
        groups.setdefault(_signature(candidate), []).append(ranked)

    # Stage 2 — per signature, promote the best weapon; keep the rest as alts.
    winners: list[RankedBuild] = []
    for group in groups.values():
        group.sort(key=_ranking_key, reverse=True)
        best = group[0]
        alternatives = [
            WeaponAlternative(
                weapon=r.build.weapon.slug,
                est_dps=r.damage.est_dps,
                raw_dps=r.damage.raw_dps,
            )
            for r in group[1:6]  # up to 5 alternative weapons
        ]
        winners.append(best.model_copy(update={"weapon_alternatives": alternatives}))

    winners.sort(key=_ranking_key, reverse=True)
    return winners[: opts.top_k]


# --- internals --------------------------------------------------------------


def _signature(build: Build) -> tuple[str, ...]:
    """Identify a build by its picto + lumina loadout.

    Skills are inventory-wide (same list for every candidate in a run), so
    excluding them keeps the key short without losing uniqueness.
    Weapons are intentionally excluded — the whole point is to dedup them.
    """
    pictos = tuple(sorted(p.slug for p in build.pictos))
    luminas = tuple(sorted(lu.slug for lu in build.luminas))
    return (*pictos, "/", *luminas)


def _ranking_key(ranked: RankedBuild) -> tuple[float, float]:
    """Order by est_dps, break ties on raw_dps — so when several builds cap
    at the same ceiling the one with the most headroom comes first."""
    return (ranked.damage.est_dps, ranked.damage.raw_dps)


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
    """Clamp est_dps to the build's rotation ceiling — keeping raw_dps intact
    so the ranking tie-break can still tell the candidates apart."""
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
        raw_dps=damage.raw_dps,
    )


def _apply_synergy(damage: DamageEstimate, multiplier: float) -> DamageEstimate:
    if multiplier == 1.0:
        return damage
    ratio = multiplier / damage.synergy_mult
    return DamageEstimate(
        base=damage.base,
        might_mult=damage.might_mult,
        picto_mult=damage.picto_mult,
        lumina_mult=damage.lumina_mult,
        crit_mult=damage.crit_mult,
        synergy_mult=multiplier,
        est_dps=damage.est_dps * ratio,
        raw_dps=damage.raw_dps * ratio,
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
    if damage.is_capped:
        reasons.append(
            f"Cap hit — raw {damage.raw_dps:.0f} clamped to {damage.est_dps:.0f} "
            f"(9999 per hit)."
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
