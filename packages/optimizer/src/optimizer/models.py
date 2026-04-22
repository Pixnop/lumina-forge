"""Optimizer domain models.

The optimizer reads the vault markdown directly (via :mod:`optimizer.vault`)
so its domain model is not coupled to the scraper's internal types — both
sides meet at the YAML frontmatter format.

Vault item shapes (:class:`PictoItem`, :class:`WeaponItem`, etc.) are
deliberately lenient: they cover the fields the scorer uses and let anything
else live in ``extra`` without failing validation.
"""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Mode = Literal["dps", "utility", "balanced"]


# --- vault-side items -------------------------------------------------------


class _VaultItem(BaseModel):
    """Common shape for anything loaded from the vault."""

    model_config = ConfigDict(extra="allow")

    slug: str
    name: str
    sources: list[str] = Field(default_factory=list)
    body: str = ""


class PictoItem(_VaultItem):
    category: str | None = None
    effect: str = ""
    effect_structured: dict[str, Any] = Field(default_factory=dict)
    stats_granted: dict[str, Any] = Field(default_factory=dict)
    lumina_points_cost: int | None = None
    source_locations: list[dict[str, Any]] = Field(default_factory=list)


class LuminaItem(_VaultItem):
    category: str | None = None
    pp_cost: int | None = None
    effect: str = ""
    effect_structured: dict[str, Any] = Field(default_factory=dict)
    source_picto: str | None = None
    restrictions: list[str] = Field(default_factory=list)


class WeaponItem(_VaultItem):
    character: str | None = None
    base_damage: int | None = None
    scaling_stat: str | None = None
    boosted_skills: list[str] = Field(default_factory=list)
    passives: list[dict[str, Any]] = Field(default_factory=list)


class SkillItem(_VaultItem):
    character: str | None = None
    ap_cost: int | None = None
    ap_generated: int | None = None
    category: str | None = None
    targeting: str | None = None
    element: str | None = None
    hits: int | None = None
    cooldown: int | None = None


class CharacterItem(_VaultItem):
    role: str | None = None
    primary_stat: str | None = None
    signature_skills: list[str] = Field(default_factory=list)
    archetypes: list[str] = Field(default_factory=list)
    base_stats: dict[str, int] = Field(default_factory=dict)


class SynergyItem(_VaultItem):
    tier: str | None = None
    components: dict[str, Any] = Field(default_factory=dict)
    effect_summary: str = ""
    score_bonus: float = 0.0


class FormulaItem(_VaultItem):
    """Notes under ``Formulas/`` — carry the damage-math constants the engine consumes."""

    variables: list[str] = Field(default_factory=list)
    applies_to: str = ""
    effect_structured: dict[str, Any] = Field(default_factory=dict)


# --- inventory (user input) -------------------------------------------------


class Attributes(BaseModel):
    """In-game attribute allocation. Everything defaults to zero."""

    model_config = ConfigDict(extra="forbid")

    might: int = 0
    agility: int = 0
    defense: int = 0
    luck: int = 0
    vitality: int = 0


class Inventory(BaseModel):
    """Everything the user currently owns for a given character."""

    model_config = ConfigDict(extra="forbid")

    character: str
    level: int = 1
    attributes: Attributes = Field(default_factory=Attributes)
    weapons_available: list[str] = Field(default_factory=list)
    pictos_available: list[str] = Field(default_factory=list)
    pictos_mastered: list[str] = Field(default_factory=list)
    luminas_extra: list[str] = Field(default_factory=list)
    pp_budget: int = 0
    skills_known: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _mastered_subset_of_available(self) -> Self:
        extra = set(self.pictos_mastered) - set(self.pictos_available)
        if extra:
            raise ValueError(
                f"pictos_mastered must be a subset of pictos_available — "
                f"unknown: {sorted(extra)}"
            )
        return self

    def luminas_available(self) -> list[str]:
        """Luminas accessible: every mastered picto contributes its lumina,
        plus anything listed under ``luminas_extra``. Deduplicated, order
        preserved."""
        seen: set[str] = set()
        result: list[str] = []
        for slug in (*self.pictos_mastered, *self.luminas_extra):
            if slug not in seen:
                seen.add(slug)
                result.append(slug)
        return result


# --- scoring outputs --------------------------------------------------------


class DamageEstimate(BaseModel):
    model_config = ConfigDict(frozen=True)

    base: float
    might_mult: float
    picto_mult: float
    lumina_mult: float
    crit_mult: float
    synergy_mult: float
    est_dps: float

    def breakdown(self) -> dict[str, float]:
        return {
            "base": self.base,
            "might_mult": self.might_mult,
            "picto_mult": self.picto_mult,
            "lumina_mult": self.lumina_mult,
            "crit_mult": self.crit_mult,
            "synergy_mult": self.synergy_mult,
            "est_dps": self.est_dps,
        }


class UtilityScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    has_revive: bool = False
    has_heal: bool = False
    has_defense_buff: bool = False
    score_0_1: float = 0.0


class Build(BaseModel):
    """A fully-specified loadout — what we score."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    character: CharacterItem
    weapon: WeaponItem
    pictos: tuple[PictoItem, PictoItem, PictoItem]
    luminas: list[LuminaItem] = Field(default_factory=list)
    skills_used: list[SkillItem] = Field(default_factory=list)
    attributes: Attributes = Field(default_factory=Attributes)


class RankedBuild(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    build: Build
    damage: DamageEstimate
    utility: UtilityScore
    synergies_matched: list[SynergyItem] = Field(default_factory=list)
    total_score: float
    rotation_hint: list[str] = Field(default_factory=list)
    why: list[str] = Field(default_factory=list)
