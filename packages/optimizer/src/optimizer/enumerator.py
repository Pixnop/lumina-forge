"""Enumerate candidate builds: weapon × C(pictos, 3) × greedy-fill luminas."""

from __future__ import annotations

import itertools
import logging
import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import cast

from optimizer.models import (
    Attributes,
    Build,
    CharacterItem,
    Inventory,
    LuminaItem,
    PictoItem,
    SkillItem,
    WeaponItem,
)
from optimizer.vault import VaultIndex

log = logging.getLogger(__name__)

MAX_COMBOS_SAFETY: int = 10_000_000  # truncate pictos_available above this
PICTOS_PER_BUILD: int = 3


@dataclass(slots=True)
class EnumerationContext:
    character: CharacterItem
    weapons: list[WeaponItem]
    pictos: list[PictoItem]
    luminas: list[LuminaItem]
    skills: list[SkillItem]
    attributes: Attributes
    pp_budget: int


def build_context(inventory: Inventory, index: VaultIndex) -> EnumerationContext:
    """Resolve inventory slugs to vault items, keeping only what's valid."""
    character = _resolve_character(inventory, index)

    weapons = _resolve_many(inventory.weapons_available, index.weapons, "weapon")
    # Only weapons compatible with the active character survive the enumeration.
    target_char = character.slug.lower()
    weapons = [
        w for w in weapons
        if (w.character or "").lower() in {"", target_char}
    ]

    pictos = _resolve_many(inventory.pictos_available, index.pictos, "picto")
    pictos = _truncate_pictos(pictos, len(weapons))

    luminas = _resolve_many(inventory.luminas_available(), index.luminas, "lumina")
    skills = _resolve_many(inventory.skills_known, index.skills, "skill")

    return EnumerationContext(
        character=character,
        weapons=weapons,
        pictos=pictos,
        luminas=luminas,
        skills=skills,
        attributes=inventory.attributes,
        pp_budget=inventory.pp_budget,
    )


def enumerate_builds(ctx: EnumerationContext) -> Iterator[Build]:
    if not ctx.weapons:
        log.warning("optimizer: no weapons in inventory — nothing to enumerate")
        return
    if len(ctx.pictos) < PICTOS_PER_BUILD:
        log.warning(
            "optimizer: only %d pictos — need at least %d", len(ctx.pictos), PICTOS_PER_BUILD
        )
        return

    sorted_luminas = _sort_luminas_by_value(ctx.luminas)
    for weapon in ctx.weapons:
        for combo in itertools.combinations(ctx.pictos, PICTOS_PER_BUILD):
            luminas = _greedy_fill_luminas(sorted_luminas, ctx.pp_budget)
            yield Build(
                character=ctx.character,
                weapon=weapon,
                # combo has exactly PICTOS_PER_BUILD items by construction,
                # but itertools.combinations is typed as tuple[T, ...] only.
                pictos=cast("tuple[PictoItem, PictoItem, PictoItem]", combo),
                luminas=luminas,
                skills_used=list(ctx.skills),
                attributes=ctx.attributes,
            )


# --- helpers ----------------------------------------------------------------


def _resolve_character(inventory: Inventory, index: VaultIndex) -> CharacterItem:
    character = index.characters.get(inventory.character)
    if character is None:
        raise ValueError(
            f"character {inventory.character!r} not found in vault "
            f"(known: {sorted(index.characters)})"
        )
    return character


def _resolve_many[T](slugs: list[str], index: Mapping[str, T], kind: str) -> list[T]:
    resolved: list[T] = []
    missing: list[str] = []
    for slug in slugs:
        item = index.get(slug)
        if item is None:
            missing.append(slug)
            continue
        resolved.append(item)
    if missing:
        log.warning("optimizer: %d unknown %s slugs skipped: %s", len(missing), kind, missing[:5])
    return resolved


def _truncate_pictos(pictos: list[PictoItem], weapon_count: int) -> list[PictoItem]:
    """If the search space is wider than MAX_COMBOS_SAFETY, keep the pictos
    that look strongest first (those with non-empty effect_structured or
    dense stat grants). Deterministic — no randomness."""
    n_pictos = max(len(pictos), PICTOS_PER_BUILD)
    estimated = (weapon_count or 1) * math.comb(n_pictos, PICTOS_PER_BUILD)
    if estimated <= MAX_COMBOS_SAFETY:
        return pictos
    pictos_sorted = sorted(pictos, key=_picto_standalone_score, reverse=True)
    budget = max(
        PICTOS_PER_BUILD + 1,
        _max_pictos_under_budget(weapon_count or 1),
    )
    log.warning(
        "optimizer: truncating pictos from %d to %d — combinatorial safety",
        len(pictos),
        budget,
    )
    return pictos_sorted[:budget]


def _max_pictos_under_budget(weapon_count: int) -> int:
    """Largest ``n`` such that ``weapon_count × C(n, 3) ≤ MAX_COMBOS_SAFETY``."""
    per_weapon_budget = MAX_COMBOS_SAFETY // max(weapon_count, 1)
    n = PICTOS_PER_BUILD
    while math.comb(n + 1, PICTOS_PER_BUILD) <= per_weapon_budget:
        n += 1
    return n


def _picto_standalone_score(picto: PictoItem) -> float:
    """Rough priority key when we have to drop pictos from the search."""
    structured = sum(
        float(v) for v in picto.effect_structured.values() if isinstance(v, int | float)
    )
    density = len(picto.stats_granted) * 0.05
    offensive = 1.0 if picto.category == "Offensive" else 0.0
    return structured + density + offensive


def _sort_luminas_by_value(luminas: list[LuminaItem]) -> list[LuminaItem]:
    """Sort luminas by estimated value-per-PP descending. Zero-cost luminas
    sort to the front. Uses a heuristic identical to the one in formulas.py
    so the enumerator's view of lumina value matches the scorer's."""
    from optimizer.formulas import _picto_contribution

    def key(lumina: LuminaItem) -> float:
        contribution = _picto_contribution(lumina.effect_structured, lumina.effect)
        cost = float(lumina.pp_cost or 1)
        return contribution / cost

    return sorted(luminas, key=key, reverse=True)


def _greedy_fill_luminas(sorted_luminas: list[LuminaItem], pp_budget: int) -> list[LuminaItem]:
    picked: list[LuminaItem] = []
    remaining = pp_budget
    for lumina in sorted_luminas:
        cost = int(lumina.pp_cost or 0)
        if cost <= remaining:
            picked.append(lumina)
            remaining -= cost
        if remaining <= 0:
            break
    return picked
