"""Wire format for the /optimize endpoint — kept thin on top of the engine models."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from optimizer.models import (
    ArchetypeMatch,
    AspirationalBuild,
    DamageEstimate,
    Inventory,
    Mode,
    UtilityScore,
)
from optimizer.rotation_sim import RotationTrace

# --- request ----------------------------------------------------------------


class OptimizeRequest(BaseModel):
    """Everything the engine needs to rank a single inventory."""

    model_config = ConfigDict(extra="forbid")

    inventory: Inventory
    top: Annotated[int, Field(ge=1, le=50)] = 5
    mode: Mode = "dps"
    weight_utility: Annotated[float | None, Field(ge=0.0, le=1.0)] = None


# --- response ---------------------------------------------------------------


class BuildLoadout(BaseModel):
    """Minimal identity of a build — slugs only, the client resolves names."""

    model_config = ConfigDict(extra="forbid")

    character: str
    weapon: str
    weapon_level: int | None = None
    pictos: list[str]
    luminas: list[str]
    skills_used: list[str]
    # Sum of pp_cost across the slotted luminas, alongside the inventory's
    # cap. Surfaces how much of the player's lumina budget the engine
    # actually consumed so they can spot under-utilization at a glance.
    pp_used: int = 0
    pp_budget: int = 0


class WeaponAlternativeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weapon: str
    est_dps: float
    raw_dps: float


class DeckVariantResponse(BaseModel):
    """Near-duplicate build with ≥2 pictos in common with the parent."""

    model_config = ConfigDict(extra="forbid")

    weapon: str
    pictos: list[str]
    luminas: list[str]
    est_dps: float
    raw_dps: float


class RankedBuildResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int
    total_score: float
    loadout: BuildLoadout
    damage: DamageEstimate
    utility: UtilityScore
    synergies_matched: list[str]
    rotation_hint: list[str]
    why: list[str]
    weapon_alternatives: list[WeaponAlternativeResponse] = []
    deck_variants: list[DeckVariantResponse] = []
    archetype: ArchetypeMatch | None = None
    rotation_trace: RotationTrace | None = None


class OptimizeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    builds: list[RankedBuildResponse]
    aspirational: list[AspirationalBuild] = []
    total_enumerated: int | None = None


# --- team optimize ----------------------------------------------------------


class TeamOptimizeRequest(BaseModel):
    """Optimize a 2- or 3-character party. Each inventory is a full
    single-character inventory; the team optimizer pools their luminas
    and enforces picto disjointness across members."""

    model_config = ConfigDict(extra="forbid")

    inventories: Annotated[list[Inventory], Field(min_length=2, max_length=3)]
    top: Annotated[int, Field(ge=1, le=20)] = 5
    mode: Mode = "dps"
    weight_utility: Annotated[float | None, Field(ge=0.0, le=1.0)] = None


class TeamMemberResponse(BaseModel):
    """One slot of a team result. ``inventory_index`` is the position of
    the source inventory in the request (0-based), so the UI can match
    the build back to the character card the user picked it for."""

    model_config = ConfigDict(extra="forbid")

    inventory_index: int
    build: RankedBuildResponse


class TeamBuildResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    members: list[TeamMemberResponse]
    total_score: float


class TeamOptimizeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    teams: list[TeamBuildResponse]


# --- info / health ----------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class VaultInfoResponse(BaseModel):
    characters: int
    pictos: int
    weapons: int
    luminas: int
    skills: int
    synergies: int


class VaultItem(BaseModel):
    """Projection of a vault entry — enough for autocomplete *and* the KB browser."""

    slug: str
    name: str
    category: str | None = None
    character: str | None = None
    pp_cost: int | None = None
    ap_cost: int | None = None
    base_damage: int | None = None
    # Fuller fields for the in-app browser. Optional so autocomplete calls
    # can skip them when they're not needed.
    effect: str | None = None
    effect_structured: dict[str, object] | None = None
    stats_granted: dict[str, int] | None = None
    scaling_stat: str | None = None
    passives: list[dict[str, object]] | None = None
    # Path under ``/assets`` where the item's scraped image is served —
    # e.g. ``Pictos/augmented-critical.png``. None when no image was
    # scraped or downloaded yet.
    image_path: str | None = None


class VaultItemsResponse(BaseModel):
    items: list[VaultItem]
