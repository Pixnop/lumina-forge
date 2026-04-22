"""Minimal rotation simulator.

The old damage model assumed a flat 3 hits per rotation. Real builds
differ wildly: a dual-wield Verso skill fires 6+ hits per cast while
Gustave's Overcharge hits once per cast but for hard-capped damage.

This sim keeps it simple:

1. Compute an AP budget for the full rotation (starting AP + per-turn
   regen + bonuses from pictos/luminas/weapon passives).
2. Pick the *most-damage-per-AP* skill the build knows (the dominant
   strategy in E33's cap-constrained environment).
3. Fit as many casts of that skill into the budget as possible (at
   least one).
4. Total hits = casts × hits-per-cast. Multiply by ``weapon.base_damage``
   to produce the rotation's base number.

This replaces the flat ``× rotation_turns`` assumption in the scorer
without tipping into a full action-by-action simulator. A proper
simulator (multi-skill sequencing, turn-order, status ticks) is
v0.5.x territory.
"""

from __future__ import annotations

from optimizer.models import Build, SkillItem

# Same trigger-frequency table the scorer uses for ap_mult. Kept separate
# so tweaking one won't silently shift the other.
_AP_TRIGGER_FREQ_PER_TURN: dict[str, float] = {
    "battle_start": 0.0,  # accounted per-rotation, not per-turn
    "turn_start": 1.0,
    "base_attack": 1.0,
    "on_kill": 0.4,
    "on_break": 0.3,
    "on_death": 0.1,
    "parry": 0.4,
    "perfect_dodge": 0.2,
    "counter": 0.3,
    "critical_hit": 0.3,
    "free_aim": 0.3,
    "on_status_applied": 0.3,
    "on_dot_applied": 0.3,
    "on_buff_applied": 0.2,
    "vs_marked": 0.4,
    "vs_stunned": 0.3,
    "vs_burning": 0.5,
    "vs_weakness": 0.3,
    "solo": 0.0,
    "low_hp": 0.1,
}

# Conservative baseline — the game normally hands out 3 starting AP and
# one AP per turn from parry/basic-attack flow.
BASELINE_STARTING_AP: float = 3.0
BASELINE_PER_TURN_AP: float = 1.0
DEFAULT_SKILL_AP_COST: int = 3
FALLBACK_HITS_PER_ROTATION: int = 3


def total_hits_per_rotation(build: Build, rotation_turns: int) -> int:
    """Best-skill casts × hits-per-cast. Falls back to the flat baseline
    when the build has no usable skills with hit counts."""
    offensive_skills = [s for s in build.skills_used if _is_offensive(s)]
    if not offensive_skills:
        return FALLBACK_HITS_PER_ROTATION * rotation_turns // max(rotation_turns, 1) or 1

    budget = _ap_budget_per_rotation(build, rotation_turns)
    best = max(offensive_skills, key=_skill_value)
    ap_cost = max(int(best.ap_cost or DEFAULT_SKILL_AP_COST), 1)
    hits_per_cast = max(int(best.hits or 1), 1)

    casts = int(budget // ap_cost)
    casts = max(casts, 1)  # even a short rotation casts at least once
    return casts * hits_per_cast


def _is_offensive(skill: SkillItem) -> bool:
    """Only skills that actually deal damage should feed the sim."""
    if skill.hits is None or skill.hits <= 0:
        return False
    category = (skill.category or "").lower()
    return category not in {"buff", "heal", "utility", "support"}


def _skill_value(skill: SkillItem) -> float:
    """Damage-per-AP proxy — higher is better."""
    hits = max(int(skill.hits or 1), 1)
    ap_cost = max(int(skill.ap_cost or DEFAULT_SKILL_AP_COST), 1)
    return hits / ap_cost


def _ap_budget_per_rotation(build: Build, rotation_turns: int) -> float:
    """Starting AP + per-turn regen + all AP bonuses from pictos / luminas /
    weapon passives, weighted by trigger frequency."""
    budget = BASELINE_STARTING_AP + BASELINE_PER_TURN_AP * rotation_turns
    for container in (*build.pictos, *build.luminas):
        budget += _ap_from_effect(
            getattr(container, "effect_structured", {}) or {}, rotation_turns
        )
    for passive in getattr(build.weapon, "passives", []) or []:
        if isinstance(passive, dict):
            budget += _ap_from_effect(
                passive.get("effect_structured", {}) or {}, rotation_turns
            )
    return budget


def _ap_from_effect(effect_structured: dict[str, object], rotation_turns: int) -> float:
    bonus_raw = effect_structured.get("ap_bonus")
    if not isinstance(bonus_raw, int | float):
        return 0.0
    bonus = float(bonus_raw)
    trigger_raw = effect_structured.get("ap_trigger")
    trigger = trigger_raw.lower() if isinstance(trigger_raw, str) else ""
    if trigger == "battle_start":
        return bonus
    freq = _AP_TRIGGER_FREQ_PER_TURN.get(trigger, 0.2)
    return bonus * freq * rotation_turns
