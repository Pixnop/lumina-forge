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
    pictos: list[str]
    luminas: list[str]
    skills_used: list[str]


class WeaponAlternativeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weapon: str
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
    archetype: ArchetypeMatch | None = None


class OptimizeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    builds: list[RankedBuildResponse]
    aspirational: list[AspirationalBuild] = []
    total_enumerated: int | None = None


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
    """Thin projection of a vault entry — enough for autocomplete UIs."""

    slug: str
    name: str
    category: str | None = None
    character: str | None = None
    pp_cost: int | None = None
    ap_cost: int | None = None
    base_damage: int | None = None


class VaultItemsResponse(BaseModel):
    items: list[VaultItem]
