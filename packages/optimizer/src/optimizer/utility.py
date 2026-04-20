"""Detect utility value in a build (revive / heal / defensive buffs).

The optimizer's default ranking is pure DPS, but a user can boost utility
weight via ``--weight-utility 0.2``. This module produces a score in [0, 1]
that multiplies the final ranking.
"""

from __future__ import annotations

from dataclasses import dataclass

from optimizer.models import Build, UtilityScore

_REVIVE = ("revive", "second chance", "resurrect")
_HEAL = ("heal", "healing", "restore hp", "regen")
_DEFENSE = ("shield", "defense up", "damage reduction", "barrier", "invulnerability")


@dataclass(frozen=True, slots=True)
class UtilityScorer:
    """Sum keyword-based utility hits and normalise to [0, 1]."""

    weight_revive: float = 0.5
    weight_heal: float = 0.3
    weight_defense: float = 0.2

    def score(self, build: Build) -> UtilityScore:
        texts = list(self._effect_texts(build))
        has_revive = any(_contains_any(t, _REVIVE) for t in texts)
        has_heal = any(_contains_any(t, _HEAL) for t in texts)
        has_defense = any(_contains_any(t, _DEFENSE) for t in texts)
        score = (
            (self.weight_revive if has_revive else 0.0)
            + (self.weight_heal if has_heal else 0.0)
            + (self.weight_defense if has_defense else 0.0)
        )
        return UtilityScore(
            has_revive=has_revive,
            has_heal=has_heal,
            has_defense_buff=has_defense,
            score_0_1=min(1.0, score),
        )

    @staticmethod
    def _effect_texts(build: Build) -> list[str]:
        texts: list[str] = []
        for p in build.pictos:
            if p.effect:
                texts.append(p.effect)
        for lu in build.luminas:
            if lu.effect:
                texts.append(lu.effect)
        return texts


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(kw in low for kw in keywords)
