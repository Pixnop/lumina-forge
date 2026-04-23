"""Rotation simulator v2: turn-by-turn, status-aware, with a trace."""

from __future__ import annotations

from optimizer.models import Attributes, Build, CharacterItem, PictoItem, SkillItem, WeaponItem
from optimizer.rotation_sim import simulate, total_hits_per_rotation


def _skill(slug: str, hits: int, ap_cost: int, category: str = "Offensive") -> SkillItem:
    return SkillItem(
        slug=slug,
        name=slug,
        character="x",
        hits=hits,
        ap_cost=ap_cost,
        category=category,
    )


def _build(
    skills: list[SkillItem] | None = None,
    pictos: tuple[PictoItem, ...] | None = None,
) -> Build:
    character = CharacterItem(slug="x", name="X")
    weapon = WeaponItem(slug="w", name="W", base_damage=100)
    neutral = PictoItem(slug="p", name="P", effect="neutral")
    return Build(
        character=character,
        weapon=weapon,
        pictos=pictos or (neutral, neutral, neutral),
        luminas=[],
        skills_used=skills or [],
        attributes=Attributes(),
    )


def test_fallback_when_no_skills() -> None:
    hits = total_hits_per_rotation(_build(skills=[]), rotation_turns=3)
    # Baseline: 3 hits for the rotation (roughly 1/turn).
    assert hits >= 1


def test_picks_skill_with_best_damage_per_ap() -> None:
    """Greedy-per-turn: takes the burst when AP allows, falls back to
    cheap on low-AP turns."""
    cheap_low = _skill("cheap", hits=1, ap_cost=1)
    expensive_multi = _skill("burst", hits=6, ap_cost=3)
    b = _build(skills=[cheap_low, expensive_multi])
    trace = simulate(b, rotation_turns=3)

    # Starting AP 3, burst costs 3 → turn 1 casts burst (6 hits). Subsequent
    # turns regen 1 AP and can only fit cheap (1 hit each). 6 + 1 + 1 = 8.
    assert trace.total_hits == 8
    # Trace actually picks burst on turn 1, cheap on turns 2/3
    assert trace.turns[0].skill_slug == "burst"
    assert trace.turns[1].skill_slug == "cheap"


def test_bigger_ap_budget_buys_more_casts() -> None:
    burst = _skill("burst", hits=4, ap_cost=3)
    battle_start_ap_picto = PictoItem(
        slug="energising-start-iii",
        name="E",
        effect="+1 AP on battle start.",
        effect_structured={"ap_bonus": 3, "ap_trigger": "battle_start"},
    )
    baseline = _build(skills=[burst])
    boosted = _build(
        skills=[burst],
        pictos=(battle_start_ap_picto, battle_start_ap_picto, battle_start_ap_picto),
    )

    assert total_hits_per_rotation(boosted, 3) > total_hits_per_rotation(baseline, 3)


def test_buff_skills_are_skipped() -> None:
    buff = _skill("overcharge", hits=0, ap_cost=3, category="Buff")
    nuke = _skill("lumiere-assault", hits=1, ap_cost=2)
    b = _build(skills=[buff, nuke])
    trace = simulate(b, rotation_turns=3)

    # Only nuke (2 AP) considered. AP 3 → turn 1 casts nuke (ap→1). Turn 2
    # AP 1+1=2 → cast nuke (ap→0). Turn 3 AP 0+1=1 → can't afford. 2 hits.
    assert trace.total_hits == 2
    assert all(t.skill_slug in {"lumiere-assault", None} for t in trace.turns)


def test_multi_hit_skill_outpaces_single_hit_ones() -> None:
    one_hit = _skill("one", hits=1, ap_cost=2)
    many_hits = _skill("many", hits=8, ap_cost=3)
    b = _build(skills=[one_hit, many_hits])
    trace = simulate(b, rotation_turns=3)

    # Turn 1 ap=3: cast many (+8 hits), ap→0. Turn 2 ap=1: one_hit needs 2 AP
    # — can't. Turn 3 ap=2: cast one_hit (+1 hit). Total 9.
    assert trace.total_hits == 9
    assert trace.turns[0].skill_slug == "many"


# --- v2-specific behaviour --------------------------------------------------


def test_trace_captures_per_turn_details() -> None:
    skill = _skill("strike", hits=2, ap_cost=2)
    b = _build(skills=[skill])
    trace = simulate(b, rotation_turns=3)

    assert len(trace.turns) == 3
    for t in trace.turns:
        assert t.ap_start >= 0
        assert t.ap_end >= 0
        if t.skill_slug:
            assert t.skill_hits > 0
            assert t.damage_raw > 0


def test_fire_and_storm_chain_produces_stain_consumption() -> None:
    fire = SkillItem(
        slug="from-fire",
        name="From Fire",
        character="lune",
        hits=3,
        ap_cost=2,
        element="Fire",
    )
    storm = SkillItem(
        slug="strike-storm",
        name="Strike Storm",
        character="lune",
        hits=3,
        ap_cost=2,
        element="Storm",
    )
    b = _build(skills=[fire, storm])
    trace = simulate(b, rotation_turns=3)

    # Turn 1 applies a fire stain; turn 2+ storm skill should consume it for
    # +50 % on that hit. Check some turn recorded a stain consumption.
    assert any(t.stain_consumed is not None for t in trace.turns)


def test_mark_skill_applies_status() -> None:
    mark = _skill("marking-shot", hits=1, ap_cost=2)
    b = _build(skills=[mark])
    trace = simulate(b, rotation_turns=3)

    applied = [status for t in trace.turns for status in t.statuses_applied]
    assert "mark" in applied
