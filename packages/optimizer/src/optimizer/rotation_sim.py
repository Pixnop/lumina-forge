"""Turn-by-turn rotation simulator.

v2 picks up where the v1 sim left off (best skill × casts) by modelling:

- Per-turn **AP regeneration** from inventory triggers (battle_start,
  turn_start, base_attack…).
- **Status stacks** that persist across turns — Burn / Mark / Powerful
  plus elemental Stains (Fire, Storm, Earth, …). Each carries a stack
  count and a remaining-turns counter, and is consumed or boosts damage
  per the in-game rules.
- **Skill selection** per turn: the highest-damage skill the build can
  afford given active statuses, including elemental chain multipliers
  (an opposite-element skill consumes the target's Stain for +50 %).
- A **trace** — one :class:`TurnTrace` per simulated turn — surfaced to
  the UI so the player sees *why* a build scores the way it does.

This is still not a full action-accurate simulator (no Gradient bar
economy, no character-specific mechanics like Maelle's stances or
Monoco's masks). But it captures the patterns that drive the
damage-critical S-tier builds in E33.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from optimizer.models import Build, SkillItem

log = logging.getLogger(__name__)

# --- tuning knobs -----------------------------------------------------------

_AP_TRIGGER_FREQ_PER_TURN: dict[str, float] = {
    "battle_start": 0.0,  # accounted once per rotation
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

BASELINE_STARTING_AP: float = 3.0
BASELINE_PER_TURN_AP: float = 1.0
DEFAULT_SKILL_AP_COST: int = 3
FALLBACK_HITS_PER_ROTATION: int = 3

# Damage-cap per hit, same clamp the scorer applies after multipliers.
DAMAGE_CAP_PER_HIT: float = 9999.0

# Status damage contributions (per-hit multiplier while the status is active).
_STATUS_DAMAGE_MULT: dict[str, float] = {
    "powerful": 1.50,  # +50 % outgoing damage
    "mark": 1.30,  # +30 % against marked target
    "burn": 1.10,  # +10 % per stack (clamped at +50 %)
}

# Elemental stains consumed by opposing elements for +50 % on the consuming
# skill. The mapping is symmetrical: any of {fire, storm, earth, ice, light,
# dark} stain on target is consumed when a skill of a *different* element
# hits.
_ELEMENTS = frozenset({"fire", "storm", "lightning", "earth", "ice", "light", "dark", "void"})

# How long each applied status stays on the target (turns), before the
# targeted-damage multiplier stops counting. Kept conservative — these
# match the in-game durations for the basic, non-picto-extended versions.
_STATUS_DURATION_TURNS: dict[str, int] = {
    "powerful": 2,
    "mark": 3,
    "burn": 3,
    "stain": 2,
}

_STATUS_MAX_STACKS: dict[str, int] = {
    "burn": 5,
    "mark": 2,
    "powerful": 1,
    "stain": 1,
}


# --- dataclasses + pydantic wire types --------------------------------------


@dataclass(slots=True)
class StatusStack:
    kind: str  # burn, mark, powerful, stain
    stacks: int = 1
    turns_remaining: int = 3
    element: str | None = None  # only for stains

    def key(self) -> str:
        if self.kind == "stain" and self.element:
            return f"stain-{self.element}"
        return self.kind


class TurnTrace(BaseModel):
    """Single-turn snapshot. Pydantic so it rides out through the API."""

    model_config = ConfigDict(frozen=True)

    turn: int  # 1-based
    ap_start: float
    ap_spent: int
    ap_end: float
    skill_slug: str | None = None
    skill_name: str | None = None
    skill_hits: int = 0
    skill_element: str | None = None
    damage_raw: float = 0.0  # before cap
    damage_final: float = 0.0  # after cap
    status_mult: float = 1.0  # aggregate multiplier applied this turn
    active_statuses: list[str] = Field(default_factory=list)
    statuses_applied: list[str] = Field(default_factory=list)
    stain_consumed: str | None = None  # which elemental stain got eaten


class RotationTrace(BaseModel):
    model_config = ConfigDict(frozen=True)

    turns: list[TurnTrace] = Field(default_factory=list)
    total_hits: int = 0
    total_damage_raw: float = 0.0
    total_damage_final: float = 0.0
    fallback: bool = False  # true when the build had no usable offensive skills


# --- public API -------------------------------------------------------------


def simulate(build: Build, rotation_turns: int) -> RotationTrace:
    """Run the turn-by-turn sim and return the full trace."""
    offensive_skills = [s for s in build.skills_used if _is_offensive(s)]
    if not offensive_skills:
        return _fallback_trace(rotation_turns)

    starting_ap = BASELINE_STARTING_AP + _battle_start_ap(build)
    per_turn_regen = BASELINE_PER_TURN_AP + _per_turn_ap(build, rotation_turns) / rotation_turns

    state = _SimState(ap=starting_ap)
    turns: list[TurnTrace] = []
    total_raw = 0.0
    total_final = 0.0
    total_hits = 0

    for turn_idx in range(1, rotation_turns + 1):
        # Tick 1: decay statuses at the start of each turn except turn 1
        if turn_idx > 1:
            state.decay_statuses()

        # Tick 2: AP regen (except turn 1 — starting_ap already includes it)
        ap_start = state.ap
        if turn_idx > 1:
            state.ap += per_turn_regen
            ap_start = state.ap

        # Tick 3: pick best skill affordable with current AP + stain bonus.
        weapon_base = float(build.weapon.base_damage or 0)
        chosen, stain_consumed = _pick_skill(offensive_skills, state, weapon_base)
        if chosen is None:
            # Cannot afford even the cheapest skill — empty turn
            turns.append(
                TurnTrace(
                    turn=turn_idx,
                    ap_start=ap_start,
                    ap_spent=0,
                    ap_end=state.ap,
                    active_statuses=state.render_active(),
                )
            )
            continue

        ap_cost = max(int(chosen.ap_cost or DEFAULT_SKILL_AP_COST), 1)
        state.ap = max(0.0, state.ap - ap_cost)

        # Tick 4: compute damage
        hits = max(int(chosen.hits or 1), 1)
        status_mult = state.current_damage_mult(chosen)
        if stain_consumed:
            status_mult *= 1.50
            state.consume_stain(stain_consumed)

        per_hit = weapon_base * status_mult
        turn_raw = per_hit * hits
        turn_final = min(per_hit, DAMAGE_CAP_PER_HIT) * hits

        # Tick 5: apply statuses the skill triggers (element → stain, etc.)
        applied = state.apply_skill_effects(chosen)

        turns.append(
            TurnTrace(
                turn=turn_idx,
                ap_start=ap_start,
                ap_spent=ap_cost,
                ap_end=state.ap,
                skill_slug=chosen.slug,
                skill_name=chosen.name,
                skill_hits=hits,
                skill_element=(chosen.element or "").lower() or None,
                damage_raw=turn_raw,
                damage_final=turn_final,
                status_mult=status_mult,
                active_statuses=state.render_active(),
                statuses_applied=applied,
                stain_consumed=stain_consumed,
            )
        )
        total_raw += turn_raw
        total_final += turn_final
        total_hits += hits

    return RotationTrace(
        turns=turns,
        total_hits=total_hits,
        total_damage_raw=total_raw,
        total_damage_final=total_final,
    )


def total_hits_per_rotation(build: Build, rotation_turns: int) -> int:
    """Back-compat wrapper — the scorer still asks 'how many hits total?'.

    Returns the simulator's total hit count so existing callers see a
    plausibly-sized value. The scorer applies its multipliers on top.
    """
    trace = simulate(build, rotation_turns)
    return max(trace.total_hits, 1)


# --- internals --------------------------------------------------------------


@dataclass(slots=True)
class _SimState:
    ap: float
    statuses: list[StatusStack] = field(default_factory=list)

    def decay_statuses(self) -> None:
        next_statuses: list[StatusStack] = []
        for s in self.statuses:
            turns = s.turns_remaining - 1
            if turns <= 0:
                continue
            next_statuses.append(StatusStack(s.kind, s.stacks, turns, s.element))
        self.statuses = next_statuses

    def active_stain(self) -> StatusStack | None:
        for s in self.statuses:
            if s.kind == "stain":
                return s
        return None

    def consume_stain(self, element: str) -> None:
        self.statuses = [
            s for s in self.statuses
            if not (s.kind == "stain" and s.element == element)
        ]

    def current_damage_mult(self, skill: SkillItem) -> float:
        mult = 1.0
        for s in self.statuses:
            base = _STATUS_DAMAGE_MULT.get(s.kind, 1.0)
            if base <= 1.0:
                continue
            # Burn stacks cumulatively (capped at +50%). Mark and Powerful
            # apply their flat multiplier regardless of stack count.
            if s.kind == "burn":
                per_stack = base - 1.0
                mult *= 1.0 + min(per_stack * s.stacks, 0.50)
            else:
                mult *= base
        # Skill element vs stain: caller handles the +50% on stain match —
        # but we account for a base of 1.0 here so other multipliers compose.
        return mult

    def apply_skill_effects(self, skill: SkillItem) -> list[str]:
        """Figure out which statuses the skill puts on the target. Pragmatic
        heuristic — the category/element/slug/name suffice for most E33
        skills without a lookup table."""
        applied: list[str] = []
        slug = (skill.slug or "").lower()
        name = (skill.name or "").lower()
        element = (skill.element or "").lower()
        category = (skill.category or "").lower()

        # Powerful buffs — typical slugs: 'overcharge', 'powerful', 'mayhem'
        if "powerful" in slug or "powerful" in name or category == "buff":
            self._apply("powerful")
            applied.append("powerful")

        # Mark application
        if "mark" in slug or "mark" in name:
            self._apply("mark")
            applied.append("mark")

        # Burn application — 'immolation', 'burn', 'from-fire', etc.
        if "burn" in slug or "immolat" in slug or "wildfire" in slug:
            self._apply("burn")
            applied.append("burn")

        # Elemental stain from skill element
        if element in _ELEMENTS:
            self._apply("stain", element=element)
            applied.append(f"stain-{element}")
        elif "from-fire" in slug or "fire" in slug:
            self._apply("stain", element="fire")
            applied.append("stain-fire")
        elif "strike-storm" in slug or "storm" in slug or "lightning" in slug:
            self._apply("stain", element="storm")
            applied.append("stain-storm")

        return applied

    def _apply(self, kind: str, element: str | None = None) -> None:
        duration = _STATUS_DURATION_TURNS.get(kind, 3)
        cap = _STATUS_MAX_STACKS.get(kind, 1)
        # Refresh existing status or add new one
        for s in self.statuses:
            if s.kind == kind and s.element == element:
                s.stacks = min(s.stacks + 1, cap)
                s.turns_remaining = duration
                return
        self.statuses.append(
            StatusStack(
                kind=kind, stacks=1, turns_remaining=duration, element=element
            )
        )

    def render_active(self) -> list[str]:
        parts: list[str] = []
        for s in self.statuses:
            if s.kind == "stain":
                parts.append(f"stain-{s.element} ({s.turns_remaining}t)")
            elif s.stacks > 1:
                parts.append(f"{s.kind} ×{s.stacks} ({s.turns_remaining}t)")
            else:
                parts.append(f"{s.kind} ({s.turns_remaining}t)")
        return parts


def _pick_skill(
    skills: list[SkillItem], state: _SimState, weapon_base: float
) -> tuple[SkillItem | None, str | None]:
    """Return the highest-expected-damage affordable skill + stain to consume."""
    affordable = [
        s for s in skills
        if (s.ap_cost or DEFAULT_SKILL_AP_COST) <= state.ap + 1e-6
    ]
    if not affordable:
        return None, None

    active_stain = state.active_stain()

    def score(skill: SkillItem) -> float:
        hits = max(int(skill.hits or 1), 1)
        ap_cost = max(int(skill.ap_cost or DEFAULT_SKILL_AP_COST), 1)
        element = (skill.element or "").lower()
        mult = state.current_damage_mult(skill)
        # Bonus if this skill can consume the active stain
        if active_stain and active_stain.element and element and element != active_stain.element:
            mult *= 1.50
        damage = weapon_base * mult * hits
        # Damage per AP — the standard E33 tiebreaker
        return damage / ap_cost

    best = max(affordable, key=score)
    element = (best.element or "").lower()
    stain_consumed: str | None = None
    if active_stain and active_stain.element and element and element != active_stain.element:
        stain_consumed = active_stain.element

    return best, stain_consumed


def _is_offensive(skill: SkillItem) -> bool:
    if skill.hits is None or skill.hits <= 0:
        return False
    category = (skill.category or "").lower()
    return category not in {"buff", "heal", "utility", "support"}


def _fallback_trace(rotation_turns: int) -> RotationTrace:
    """No usable offensive skills — preserve the pre-sim baseline of roughly
    1 hit per turn so the scorer doesn't spike or crater for builds whose
    character hasn't unlocked their damage kit yet.
    """
    _ = rotation_turns
    return RotationTrace(
        turns=[],
        total_hits=FALLBACK_HITS_PER_ROTATION,
        total_damage_raw=0.0,
        total_damage_final=0.0,
        fallback=True,
    )


def _battle_start_ap(build: Build) -> float:
    """One-shot AP bonuses that fire at battle start."""
    total = 0.0
    for container in (*build.pictos, *build.luminas):
        total += _battle_start_bonus(getattr(container, "effect_structured", {}) or {})
    for passive in getattr(build.weapon, "passives", []) or []:
        if isinstance(passive, dict):
            total += _battle_start_bonus(passive.get("effect_structured", {}) or {})
    return total


def _battle_start_bonus(effect_structured: dict[str, Any]) -> float:
    bonus = effect_structured.get("ap_bonus")
    trigger = effect_structured.get("ap_trigger")
    if (
        isinstance(bonus, int | float)
        and isinstance(trigger, str)
        and trigger.lower() == "battle_start"
    ):
        return float(bonus)
    return 0.0


def _per_turn_ap(build: Build, rotation_turns: int) -> float:
    """Per-rotation AP contribution from non-battle-start triggers."""
    total = 0.0
    for container in (*build.pictos, *build.luminas):
        total += _per_turn_bonus(
            getattr(container, "effect_structured", {}) or {}, rotation_turns
        )
    for passive in getattr(build.weapon, "passives", []) or []:
        if isinstance(passive, dict):
            total += _per_turn_bonus(
                passive.get("effect_structured", {}) or {}, rotation_turns
            )
    return total


def _per_turn_bonus(effect_structured: dict[str, Any], rotation_turns: int) -> float:
    bonus_raw = effect_structured.get("ap_bonus")
    trigger_raw = effect_structured.get("ap_trigger")
    if not isinstance(bonus_raw, int | float) or not isinstance(trigger_raw, str):
        return 0.0
    trigger = trigger_raw.lower()
    if trigger == "battle_start":
        return 0.0  # handled separately
    freq = _AP_TRIGGER_FREQ_PER_TURN.get(trigger, 0.2)
    return float(bonus_raw) * freq * rotation_turns
