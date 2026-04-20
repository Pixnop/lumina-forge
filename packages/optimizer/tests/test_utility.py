"""UtilityScorer keyword detection."""

from __future__ import annotations

from optimizer.models import Attributes, Build, CharacterItem, LuminaItem, PictoItem, WeaponItem
from optimizer.utility import UtilityScorer


def _build(pictos: tuple[PictoItem, PictoItem, PictoItem], luminas: list[LuminaItem]) -> Build:
    return Build(
        character=CharacterItem(slug="x", name="X"),
        weapon=WeaponItem(slug="w", name="W", base_damage=100),
        pictos=pictos,
        luminas=luminas,
        skills_used=[],
        attributes=Attributes(),
    )


def test_detects_revive_and_heal() -> None:
    revive = PictoItem(slug="r", name="R", effect="Revive with 50% HP once per battle.")
    heal = LuminaItem(slug="h", name="H", effect="Healing effects restore more HP.")
    neutral = PictoItem(slug="n", name="N", effect="deal damage")
    build = _build((revive, neutral, neutral), [heal])
    score = UtilityScorer().score(build)
    assert score.has_revive is True
    assert score.has_heal is True
    assert score.has_defense_buff is False
    assert 0.0 < score.score_0_1 <= 1.0


def test_offensive_only_scores_zero() -> None:
    offensive = PictoItem(slug="o", name="O", effect="Deal double damage.")
    build = _build((offensive, offensive, offensive), [])
    score = UtilityScorer().score(build)
    assert score.has_revive is False
    assert score.has_heal is False
    assert score.score_0_1 == 0.0


def test_score_clamped_to_one() -> None:
    revive = PictoItem(slug="r", name="R", effect="revive")
    heal = LuminaItem(slug="h", name="H", effect="healing")
    shield = LuminaItem(slug="s", name="S", effect="shield and damage reduction")
    build = _build((revive, revive, revive), [heal, shield])
    score = UtilityScorer().score(build)
    assert score.score_0_1 == 1.0  # 0.5 + 0.3 + 0.2 = 1.0 exactly
