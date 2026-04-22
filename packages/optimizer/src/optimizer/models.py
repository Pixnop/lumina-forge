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

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Mode = Literal["dps", "utility", "balanced"]

DpsTier = Literal["S", "A", "B", "C", "D"]


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


class CuratedBuild(_VaultItem):
    """A hand-curated archetype under ``Builds/`` — used as a known-good reference.

    Slugs in ``weapon``, ``pictos``, ``luminas``, ``required_skills`` are
    stored bare (no ``Pictos/`` / ``Weapons/`` prefix) so they compare
    directly against the other indices.
    """

    character: str | None = None
    archetype: str | None = None
    role: str | None = None
    dps_tier: DpsTier | None = None
    weapon: str | None = None
    pictos: list[str] = Field(default_factory=list)
    luminas: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    attributes: dict[str, int] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("weapon", mode="before")
    @classmethod
    def _strip_weapon_prefix(cls, value: object) -> object:
        return _strip_folder_prefix(value) if isinstance(value, str) else value

    @field_validator("pictos", "luminas", "required_skills", mode="before")
    @classmethod
    def _strip_path_prefix(cls, value: object) -> object:
        if isinstance(value, list):
            return [_strip_folder_prefix(v) if isinstance(v, str) else v for v in value]
        return value


def _strip_folder_prefix(slug: str) -> str:
    """``Pictos/foo-bar`` → ``foo-bar``. Idempotent on already-bare slugs."""
    if "/" in slug:
        return slug.rsplit("/", 1)[-1].strip()
    return slug.strip()


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
    # AP economy multiplier — a build that generates lots of AP can fire
    # more skills per rotation, so its effective DPS is higher. Defaults
    # to 1.0 so older callers unaffected.
    ap_mult: float = 1.0
    # Post-cap DPS — what the player sees, clamped by the engine at the
    # in-game 9999-per-hit ceiling.
    est_dps: float
    # Pre-cap DPS — what the multipliers produce without the clamp. Used
    # as a secondary ranking key: when several builds cap at the same
    # est_dps, the one with the highest raw_dps wins because it has the
    # most margin and will still cap once conditional triggers miss.
    raw_dps: float = 0.0

    def breakdown(self) -> dict[str, float]:
        return {
            "base": self.base,
            "might_mult": self.might_mult,
            "picto_mult": self.picto_mult,
            "lumina_mult": self.lumina_mult,
            "crit_mult": self.crit_mult,
            "synergy_mult": self.synergy_mult,
            "ap_mult": self.ap_mult,
            "est_dps": self.est_dps,
            "raw_dps": self.raw_dps,
        }

    @property
    def is_capped(self) -> bool:
        return self.raw_dps > self.est_dps + 1e-6


class WeaponAlternative(BaseModel):
    """Secondary weapon choice for the same picto/lumina/skill loadout."""

    model_config = ConfigDict(frozen=True)

    weapon: str
    est_dps: float
    raw_dps: float


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


class ArchetypeMatch(BaseModel):
    """A ranked build recognised as (or close to) a curated archetype."""

    model_config = ConfigDict(frozen=True)

    slug: str
    name: str
    archetype: str | None = None
    dps_tier: DpsTier | None = None
    # ``exact``: weapon + pictos + luminas + required skills all match the
    # curated loadout. ``variant``: pictos + luminas match, weapon differs —
    # the curated build's "## Variants" section explicitly allows this.
    confidence: Literal["exact", "variant"] = "exact"
    bonus_applied: float = 0.0


class AspirationalBuild(BaseModel):
    """A curated archetype the player is close to being able to run."""

    model_config = ConfigDict(frozen=True)

    slug: str
    name: str
    character: str | None = None
    archetype: str | None = None
    dps_tier: DpsTier | None = None
    # Slugs the player is missing from their inventory, bucketed by kind
    # so the UI can render grouped hints ("Il vous manque: 1 picto, 1 skill").
    missing_pictos: list[str] = Field(default_factory=list)
    missing_luminas: list[str] = Field(default_factory=list)
    missing_weapon: str | None = None
    missing_skills: list[str] = Field(default_factory=list)

    def missing_count(self) -> int:
        return (
            len(self.missing_pictos)
            + len(self.missing_luminas)
            + (1 if self.missing_weapon else 0)
            + len(self.missing_skills)
        )


class RankedBuild(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    build: Build
    damage: DamageEstimate
    utility: UtilityScore
    synergies_matched: list[SynergyItem] = Field(default_factory=list)
    total_score: float
    rotation_hint: list[str] = Field(default_factory=list)
    why: list[str] = Field(default_factory=list)
    # Weapons with the same picto/lumina/skill loadout, ranked by raw DPS
    # descending. ``build.weapon`` is the primary pick; this list holds
    # the runners-up so the UI can show "also works with…".
    weapon_alternatives: list[WeaponAlternative] = Field(default_factory=list)
    # Set when this candidate matches a curated archetype from ``vault/Builds``.
    archetype: ArchetypeMatch | None = None
