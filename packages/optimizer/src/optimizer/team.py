"""Three-character party optimization.

The single-character ``optimize()`` ranks builds for one inventory in
isolation. Real Expedition 33 play uses a party of three — and the game
forbids two characters from equipping the same picto. Luminas, by
contrast, are passive learnings: once any character has mastered a
picto, every party member can spend their PP budget on its lumina.

This module's :func:`optimize_team` runs the per-character optimizer
against an enriched inventory (every team member sees the union of all
mastered pictos as available luminas), then brute-forces combinations
of the per-character top-K to find the highest-scoring assignment with
disjoint pictos. ``top_k`` here is the number of *team* configurations
returned, not per-character.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from optimizer.engine import EngineOptions, ProgressCallback, optimize
from optimizer.models import Inventory, RankedBuild
from optimizer.vault import VaultIndex

log = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class TeamMember:
    """One slot of a team result — pairs the chosen build with the
    inventory index it came from, so the UI knows which character card
    to render it under."""

    inventory_index: int
    build: RankedBuild


@dataclass(slots=True, frozen=True)
class TeamBuild:
    members: tuple[TeamMember, ...]
    total_score: float


@dataclass(slots=True, frozen=True)
class TeamResult:
    teams: list[TeamBuild]


# Per-character candidate pool size. With ``_combine_greedy`` we need
# enough breadth to escape the per-character scorer's tendency to
# converge on a handful of dominant pictos — 500 typically covers
# anything from a 28-picto mid-game inventory through a 134-picto
# end-game one. The greedy combiner short-circuits per seed so the cost
# is roughly O(pool × disjoint_lookup), not pool³.
_POOL_SCALE: int = 100
_MIN_POOL: int = 500


def optimize_team(
    inventories: list[Inventory],
    index: VaultIndex,
    options: EngineOptions | None = None,
    *,
    on_progress: ProgressCallback | None = None,
) -> TeamResult:
    """Rank ``top_k`` party configurations for the given inventories.

    Each team member's pictos must be disjoint from the others' (in-game
    constraint: only one character can equip a given picto at a time).
    Luminas are pooled — any picto mastered by any team member becomes
    available as a lumina to every member, paid out of that member's
    individual PP budget.
    """
    if len(inventories) < 2 or len(inventories) > 3:
        raise ValueError(
            f"team must have 2 or 3 members (got {len(inventories)})"
        )
    opts = options or EngineOptions()
    progress = on_progress or (lambda _phase, _pct: None)
    progress("preparing", 0.02)

    enriched = _share_lumina_pool(inventories)
    pool_size = max(_MIN_POOL, opts.top_k * _POOL_SCALE)
    # Disable per-member diversity filter — picto-disjoint matching is
    # the real diversity constraint at the team level, and squeezing
    # near-duplicates out before the combination search just shrinks the
    # pool of feasible parties.
    member_options = EngineOptions(
        top_k=pool_size,
        mode=opts.mode,
        weight_utility=opts.weight_utility,
        diverse_top_k=False,
    )

    # Per-member scoring. Each call walks the full enumerator at
    # roughly the same cost as the single-char endpoint, so we charge
    # 80 % of the bar across the three calls.
    candidates: list[list[RankedBuild]] = []
    for i, inv in enumerate(enriched):
        progress(
            f"scoring_member_{i + 1}",
            0.05 + 0.80 * (i / len(enriched)),
        )
        result = optimize(inv, index, member_options)
        candidates.append(result.builds)
        log.info("team: member %d candidates = %d", i, len(result.builds))

    progress("combining", 0.88)
    teams = _combine(candidates, opts.top_k)
    progress("done", 1.0)
    return TeamResult(teams=teams)


# --- internals --------------------------------------------------------------


def _share_lumina_pool(inventories: list[Inventory]) -> list[Inventory]:
    """Build a copy of each inventory whose ``luminas_extra`` covers
    every picto mastered or already-extra'd by *any* party member,
    minus the ones this character has mastered (those auto-promote to
    luminas via ``Inventory.luminas_available``)."""
    pool: set[str] = set()
    for inv in inventories:
        pool.update(inv.pictos_mastered)
        pool.update(inv.luminas_extra)
    enriched: list[Inventory] = []
    for inv in inventories:
        own_mastered = set(inv.pictos_mastered)
        new_extra = sorted(pool - own_mastered)
        enriched.append(inv.model_copy(update={"luminas_extra": new_extra}))
    return enriched


def _combine(
    candidates: list[list[RankedBuild]],
    top_k: int,
) -> list[TeamBuild]:
    """Seed-anchored disjoint-picto search.

    For each candidate of member 0 (in score order, capped to keep the
    seed pass cheap), pre-filter the other members' candidates to only
    those disjoint from the seed, then find the highest-scoring valid
    pairing between them. With three members the inner step is an
    explicit list_b × list_c brute force — small once the per-seed
    filter has removed everything that overlaps the seed pictos.

    Why this rather than a bare cartesian product: in ``balanced`` and
    ``utility`` modes the per-character scorer concentrates heavily on
    the same 2-3 dominant utility pictos (e.g. ``second-chance``,
    ``base-shield``). A naïve top-N × top-N × top-N can return zero
    valid triplets even at N=500. Anchoring on the seed and pre-filtering
    lets the search find disjoint completions whenever they exist.
    """
    sized = [
        [(rb, frozenset(p.slug for p in rb.build.pictos)) for rb in chars]
        for chars in candidates
    ]
    teams: list[TeamBuild] = []
    if len(sized) < 2:
        return teams

    seed_cap = max(top_k * 8, 50)
    for seed_idx, (seed, seed_set) in enumerate(sized[0]):
        if seed_idx >= seed_cap:
            break
        completion = _best_completion(seed_set, sized[1:])
        if completion is None:
            continue
        members = [(0, seed), *((i + 1, rb) for i, rb in enumerate(completion))]
        teams.append(_build_team(members))

    teams.sort(key=lambda t: t.total_score, reverse=True)
    # Deduplicate teams that share the same picto-loadout per member —
    # this happens when seeds differ only in weapon and the downstream
    # search lands on the same B and C for both.
    seen: set[tuple[frozenset[str], ...]] = set()
    out: list[TeamBuild] = []
    for team in teams:
        sig = tuple(
            frozenset(p.slug for p in m.build.build.pictos) for m in team.members
        )
        if sig in seen:
            continue
        seen.add(sig)
        out.append(team)
        if len(out) >= top_k:
            break
    return out


def _best_completion(
    used: frozenset[str],
    remaining: list[list[tuple[RankedBuild, frozenset[str]]]],
) -> list[RankedBuild] | None:
    """Pick the highest-scoring sequence of builds (one per remaining
    member) that's disjoint from ``used`` *and* from the choices made
    earlier in the sequence.

    For two-member teams (``len(remaining) == 1``) this reduces to a
    linear scan for the first disjoint candidate. For three-member
    teams (``len(remaining) == 2``) we pre-filter both members'
    candidates by the seed, then run a small cartesian product over the
    survivors. A flat greedy loop fails here because it can lock onto
    a member-1 pick whose pictos eliminate every member-2 candidate.
    """
    if not remaining:
        return []
    if len(remaining) == 1:
        for rb, picto_set in remaining[0]:
            if picto_set.isdisjoint(used):
                return [rb]
        return None
    # Two members left → small cartesian product on seed-compatible builds.
    list_b = [(rb, ps) for rb, ps in remaining[0] if ps.isdisjoint(used)]
    list_c = [(rb, ps) for rb, ps in remaining[1] if ps.isdisjoint(used)]
    if not list_b or not list_c:
        return None
    best: tuple[float, RankedBuild, RankedBuild] | None = None
    for rb_b, set_b in list_b:
        for rb_c, set_c in list_c:
            if not set_b.isdisjoint(set_c):
                continue
            score = rb_b.total_score + rb_c.total_score
            if best is None or score > best[0]:
                best = (score, rb_b, rb_c)
                # Member 0's seed isn't the only one the inner loop sees;
                # an early break on the first valid pair would skip strong
                # alternatives, so let it run.
    if best is None:
        return None
    return [best[1], best[2]]


def _build_team(items: list[tuple[int, RankedBuild]]) -> TeamBuild:
    members = tuple(
        TeamMember(inventory_index=idx, build=rb) for idx, rb in items
    )
    total = sum(rb.total_score for _, rb in items)
    return TeamBuild(members=members, total_score=total)


__all__ = ["TeamBuild", "TeamMember", "TeamResult", "optimize_team"]
