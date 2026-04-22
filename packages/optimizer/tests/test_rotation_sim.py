"""Rotation simulator: best-skill casts × hits-per-cast per rotation."""

from __future__ import annotations

from optimizer.models import Attributes, Build, CharacterItem, PictoItem, SkillItem, WeaponItem
from optimizer.rotation_sim import total_hits_per_rotation


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
    cheap_low = _skill("cheap", hits=1, ap_cost=1)         # 1 hit/AP
    expensive_multi = _skill("burst", hits=6, ap_cost=3)   # 2 hits/AP — winner
    b = _build(skills=[cheap_low, expensive_multi])
    hits = total_hits_per_rotation(b, rotation_turns=3)

    # Baseline budget: 3 starting + 1 × 3 turns = 6 AP → 2 casts × 6 hits = 12
    assert hits == 12


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
    # With only the nuke considered: 6 AP budget / 2 AP = 3 casts × 1 hit = 3.
    assert total_hits_per_rotation(b, rotation_turns=3) == 3


def test_multi_hit_skill_outpaces_single_hit_ones() -> None:
    one_hit = _skill("one", hits=1, ap_cost=2)
    many_hits = _skill("many", hits=8, ap_cost=3)
    b = _build(skills=[one_hit, many_hits])
    # Budget 6 AP → 2 casts of many_hits × 8 hits = 16.
    assert total_hits_per_rotation(b, rotation_turns=3) == 16
