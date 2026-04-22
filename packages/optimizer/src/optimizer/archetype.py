"""Match enumerated builds against curated archetypes from ``vault/Builds``.

The matcher gives a small ranking bias — it does not change damage numbers.
The bias is tiered (S > A > B) so curated S-tier archetypes rise above
generic builds of equivalent DPS. A weapon-swap-only deviation still counts
as a ``variant`` match (half bonus) so Gustave-Overcharge-with-Abysseram
gets recognised the same way the canonical Blodam loadout does.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from optimizer.models import (
    ArchetypeMatch,
    AspirationalBuild,
    Build,
    CuratedBuild,
    Inventory,
)

# Per-tier ranking bias applied as a multiplier on total_score. Kept small
# so the bonus nudges tie-breaks in favour of known archetypes without
# overwhelming raw DPS differences.
_TIER_BONUS: dict[str, float] = {
    "S": 0.08,
    "A": 0.05,
    "B": 0.03,
    "C": 0.01,
    "D": 0.00,
}


@dataclass(slots=True)
class ArchetypeMatcher:
    curated: tuple[CuratedBuild, ...]

    def match(
        self,
        build: Build,
        *,
        skills_known: frozenset[str],
    ) -> ArchetypeMatch | None:
        """Best match for ``build``, preferring exact over variant.

        Returns ``None`` when no curated archetype lines up.
        """
        best: ArchetypeMatch | None = None
        for curated in self.curated:
            candidate = _match_one(build, curated, skills_known)
            if candidate is None:
                continue
            if best is None or _is_better(candidate, best):
                best = candidate
        return best


def find_aspirational(
    curated: Iterable[CuratedBuild],
    inventory: Inventory,
    *,
    max_missing: int = 2,
    limit: int = 3,
) -> list[AspirationalBuild]:
    """Curated builds the player is within ``max_missing`` items of running.

    An archetype is aspirational when the player lacks at most ``max_missing``
    items (pictos, luminas, weapon, skills combined). Matches for the player's
    *current* character are returned — cross-character aspirations are out of
    scope because the inventory is keyed per character.
    """
    aspirational: list[AspirationalBuild] = []
    # Pictos only need to be *owned* (pictos_available) to be slotted — mastery
    # matters only for the lumina they produce, which is already captured in
    # ``luminas_available()``.
    pictos_have = set(inventory.pictos_available)
    luminas_have = set(inventory.luminas_available())
    weapons_have = set(inventory.weapons_available)
    skills_have = set(inventory.skills_known)
    current_char = inventory.character.lower()

    for curated_build in curated:
        if (curated_build.character or "").lower() != current_char:
            continue
        missing_pictos = [p for p in curated_build.pictos if p not in pictos_have]
        missing_luminas = [lu for lu in curated_build.luminas if lu not in luminas_have]
        missing_weapon = (
            curated_build.weapon
            if curated_build.weapon and curated_build.weapon not in weapons_have
            else None
        )
        missing_skills = [
            s for s in curated_build.required_skills if s not in skills_have
        ]

        total_missing = (
            len(missing_pictos)
            + len(missing_luminas)
            + (1 if missing_weapon else 0)
            + len(missing_skills)
        )
        if total_missing == 0 or total_missing > max_missing:
            continue
        aspirational.append(
            AspirationalBuild(
                slug=curated_build.slug,
                name=curated_build.name,
                character=curated_build.character,
                archetype=curated_build.archetype,
                dps_tier=curated_build.dps_tier,
                missing_pictos=missing_pictos,
                missing_luminas=missing_luminas,
                missing_weapon=missing_weapon,
                missing_skills=missing_skills,
            )
        )

    aspirational.sort(key=_aspirational_key)
    return aspirational[:limit]


def tier_bonus(match: ArchetypeMatch) -> float:
    """Multiplier to apply to ``total_score`` — already stored on ``bonus_applied``."""
    return match.bonus_applied


# --- internals --------------------------------------------------------------


def _match_one(
    build: Build,
    curated: CuratedBuild,
    skills_known: frozenset[str],
) -> ArchetypeMatch | None:
    if (curated.character or "").lower() != build.character.slug.lower():
        return None
    if not curated.pictos or set(curated.pictos) != {p.slug for p in build.pictos}:
        return None
    if not set(curated.luminas).issubset({lu.slug for lu in build.luminas}):
        return None
    if not set(curated.required_skills).issubset(skills_known):
        return None

    weapon_match = curated.weapon is None or curated.weapon == build.weapon.slug
    tier = curated.dps_tier or "C"
    base_bonus = _TIER_BONUS.get(tier, 0.0)
    confidence: Literal["exact", "variant"] = "exact" if weapon_match else "variant"
    bonus = base_bonus if weapon_match else base_bonus / 2.0
    return ArchetypeMatch(
        slug=curated.slug,
        name=curated.name,
        archetype=curated.archetype,
        dps_tier=curated.dps_tier,
        confidence=confidence,
        bonus_applied=bonus,
    )


_TIER_ORDER: dict[str, int] = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}


def _aspirational_key(entry: AspirationalBuild) -> tuple[int, int, str]:
    tier_rank = _TIER_ORDER.get(entry.dps_tier or "D", 4)
    return (tier_rank, entry.missing_count(), entry.slug)


def _is_better(candidate: ArchetypeMatch, incumbent: ArchetypeMatch) -> bool:
    """``candidate`` beats ``incumbent`` when it has more bonus, or the same
    bonus but an exact (non-variant) match."""
    if candidate.bonus_applied != incumbent.bonus_applied:
        return candidate.bonus_applied > incumbent.bonus_applied
    return candidate.confidence == "exact" and incumbent.confidence != "exact"
