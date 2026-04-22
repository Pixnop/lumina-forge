"""FastAPI application factory.

The vault is loaded once during the lifespan startup hook and cached on
``app.state.index``. A dedicated ``POST /vault/reload`` endpoint lets a
client swap in a newer scrape without restarting the process.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from optimizer import __version__
from optimizer.api.schemas import (
    BuildLoadout,
    HealthResponse,
    OptimizeRequest,
    OptimizeResponse,
    RankedBuildResponse,
    VaultInfoResponse,
    VaultItem,
    VaultItemsResponse,
    WeaponAlternativeResponse,
)
from optimizer.engine import EngineOptions, optimize
from optimizer.models import RankedBuild
from optimizer.vault import VaultIndex, VaultLoader

log = logging.getLogger(__name__)

# The API binds 127.0.0.1 only, so any caller already has local access.
# Use a wildcard to cover every local webview origin we might see:
# - http://localhost:5173   (Vite dev server)
# - http://localhost:1420   (Tauri dev window)
# - http://tauri.localhost  (Tauri 2 release on Windows / Linux)
# - https://tauri.localhost (Tauri 2 release on macOS)
# The `*` would conflict with allow_credentials=True per CORS, but we
# never set credentials.
DEFAULT_CORS_ORIGINS: tuple[str, ...] = ("*",)


def create_app(
    vault_dir: Path | None = None,
    *,
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS,
) -> FastAPI:
    """Build an app instance. ``vault_dir`` defaults to ``./vault`` at runtime."""
    effective_vault = vault_dir or Path("vault")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        log.info("loading vault from %s", effective_vault)
        app.state.vault_dir = effective_vault
        app.state.index = VaultLoader(effective_vault.resolve()).load()
        log.info(
            "vault loaded: %d characters, %d pictos, %d weapons, %d luminas, %d skills",
            len(app.state.index.characters),
            len(app.state.index.pictos),
            len(app.state.index.weapons),
            len(app.state.index.luminas),
            len(app.state.index.skills),
        )
        yield

    app = FastAPI(
        title="lumina-forge-api",
        version=__version__,
        description="Local HTTP API around the Expedition 33 build optimizer.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    _register_routes(app)
    return app


# --- routes -----------------------------------------------------------------


def _get_index(request: Request) -> VaultIndex:
    index = getattr(request.app.state, "index", None)
    if index is None:  # pragma: no cover — lifespan guarantees this
        raise HTTPException(status_code=503, detail="vault not loaded")
    assert isinstance(index, VaultIndex)
    return index


IndexDep = Annotated[VaultIndex, Depends(_get_index)]


def _register_routes(app: FastAPI) -> None:
    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    @app.get("/vault/info", response_model=VaultInfoResponse)
    def vault_info(index: IndexDep) -> VaultInfoResponse:
        return VaultInfoResponse(
            characters=len(index.characters),
            pictos=len(index.pictos),
            weapons=len(index.weapons),
            luminas=len(index.luminas),
            skills=len(index.skills),
            synergies=len(index.synergies),
        )

    @app.get("/vault/items", response_model=VaultItemsResponse)
    def vault_items(
        index: IndexDep,
        type: str,
        character: str | None = None,
    ) -> VaultItemsResponse:
        items = _project_items(index, type, character)
        return VaultItemsResponse(items=items)

    @app.post("/vault/reload", response_model=VaultInfoResponse)
    def vault_reload(request: Request) -> VaultInfoResponse:
        vault_dir: Path = request.app.state.vault_dir
        log.info("reloading vault from %s", vault_dir)
        index = VaultLoader(vault_dir.resolve()).load()
        request.app.state.index = index
        return VaultInfoResponse(
            characters=len(index.characters),
            pictos=len(index.pictos),
            weapons=len(index.weapons),
            luminas=len(index.luminas),
            skills=len(index.skills),
            synergies=len(index.synergies),
        )

    @app.post("/optimize", response_model=OptimizeResponse)
    def optimize_endpoint(
        body: OptimizeRequest,
        index: IndexDep,
    ) -> OptimizeResponse:
        if body.inventory.character not in index.characters:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"character {body.inventory.character!r} not found in vault "
                    f"(known: {sorted(index.characters)})"
                ),
            )
        options = EngineOptions(
            top_k=body.top,
            mode=body.mode,
            weight_utility=body.weight_utility,
        )
        result = optimize(body.inventory, index, options)
        return OptimizeResponse(
            builds=[_to_response(rank, r) for rank, r in enumerate(result.builds, start=1)],
            aspirational=list(result.aspirational),
        )


# --- helpers ----------------------------------------------------------------


_KNOWN_TYPES: frozenset[str] = frozenset({"character", "picto", "weapon", "lumina", "skill"})


def _project_items(index: VaultIndex, type: str, character: str | None) -> list[VaultItem]:
    type_low = type.lower()
    if type_low not in _KNOWN_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"unknown type {type!r}. Known: {sorted(_KNOWN_TYPES)}",
        )

    if type_low == "character":
        entries: list[VaultItem] = [
            VaultItem(slug=c.slug, name=c.name) for c in index.characters.values()
        ]
    elif type_low == "picto":
        entries = [
            VaultItem(slug=p.slug, name=p.name, category=p.category, pp_cost=p.lumina_points_cost)
            for p in index.pictos.values()
        ]
    elif type_low == "lumina":
        entries = [
            VaultItem(slug=lu.slug, name=lu.name, category=lu.category, pp_cost=lu.pp_cost)
            for lu in index.luminas.values()
        ]
    elif type_low == "weapon":
        entries = [
            VaultItem(
                slug=w.slug,
                name=w.name,
                character=w.character,
                base_damage=w.base_damage,
            )
            for w in index.weapons.values()
        ]
    else:  # skill
        entries = [
            VaultItem(
                slug=s.slug,
                name=s.name,
                character=s.character,
                category=s.category,
                ap_cost=s.ap_cost,
            )
            for s in index.skills.values()
        ]

    if character is not None:
        char_low = character.lower()
        entries = [e for e in entries if (e.character or "").lower() == char_low]
    entries.sort(key=lambda e: e.name.lower())
    return entries


def _to_response(rank: int, r: RankedBuild) -> RankedBuildResponse:
    return RankedBuildResponse(
        rank=rank,
        total_score=r.total_score,
        loadout=BuildLoadout(
            character=r.build.character.slug,
            weapon=r.build.weapon.slug,
            pictos=[p.slug for p in r.build.pictos],
            luminas=[lu.slug for lu in r.build.luminas],
            skills_used=[s.slug for s in r.build.skills_used],
        ),
        damage=r.damage,
        utility=r.utility,
        synergies_matched=[s.slug for s in r.synergies_matched],
        rotation_hint=r.rotation_hint,
        why=r.why,
        weapon_alternatives=[
            WeaponAlternativeResponse(
                weapon=a.weapon, est_dps=a.est_dps, raw_dps=a.raw_dps
            )
            for a in r.weapon_alternatives
        ],
        archetype=r.archetype,
    )
