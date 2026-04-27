"""FastAPI application factory.

The vault is loaded once during the lifespan startup hook and cached on
``app.state.index``. A dedicated ``POST /vault/reload`` endpoint lets a
client swap in a newer scrape without restarting the process.
"""

from __future__ import annotations

import asyncio
import json
import logging
import queue
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from optimizer import __version__
from optimizer.api.schemas import (
    BuildLoadout,
    DeckVariantResponse,
    HealthResponse,
    OptimizeRequest,
    OptimizeResponse,
    RankedBuildResponse,
    TeamBuildResponse,
    TeamMemberResponse,
    TeamOptimizeRequest,
    TeamOptimizeResponse,
    VaultInfoResponse,
    VaultItem,
    VaultItemsResponse,
    WeaponAlternativeResponse,
)
from optimizer.engine import EngineOptions, optimize
from optimizer.models import RankedBuild
from optimizer.team import optimize_team
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

    # Mount vault/_assets at /assets so the UI can pull item images by
    # relative path. Guarded because the tests spin up an app without an
    # on-disk vault.
    assets_dir = effective_vault / "_assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
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
            builds=[
                _to_response(
                    rank,
                    r,
                    pp_budget=body.inventory.pp_budget,
                    weapon_levels=body.inventory.weapon_levels,
                )
                for rank, r in enumerate(result.builds, start=1)
            ],
            aspirational=list(result.aspirational),
        )

    @app.post("/optimize/team", response_model=TeamOptimizeResponse)
    def optimize_team_endpoint(
        body: TeamOptimizeRequest, index: IndexDep
    ) -> TeamOptimizeResponse:
        _validate_team_inventories(body, index)
        options = EngineOptions(
            top_k=body.top, mode=body.mode, weight_utility=body.weight_utility
        )
        result = optimize_team(body.inventories, index, options)
        return TeamOptimizeResponse(
            teams=[_team_to_response(t, body.inventories) for t in result.teams]
        )

    @app.post("/optimize/team/stream")
    async def optimize_team_stream(
        body: TeamOptimizeRequest, index: IndexDep
    ) -> StreamingResponse:
        """Streaming counterpart of ``/optimize/team`` — same NDJSON
        envelope (progress / result / error) as ``/optimize/stream``."""
        _validate_team_inventories(body, index)
        options = EngineOptions(
            top_k=body.top, mode=body.mode, weight_utility=body.weight_utility
        )
        return StreamingResponse(
            _team_event_stream(body, index, options),
            media_type="application/x-ndjson",
        )

    @app.post("/optimize/stream")
    async def optimize_stream(body: OptimizeRequest, index: IndexDep) -> StreamingResponse:
        """Same payload as ``POST /optimize``, but the response is a stream
        of NDJSON events. The client gets ``{"event": "progress", ...}``
        ticks while the engine scores candidates, then a final
        ``{"event": "result", ...}`` carrying the full ``OptimizeResponse``.

        Errors arrive as ``{"event": "error", "detail": ...}`` and are
        always followed by stream close — the client should surface them
        the same way it surfaces a failed POST.
        """
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
        return StreamingResponse(
            _optimize_event_stream(body, index, options),
            media_type="application/x-ndjson",
        )


# --- helpers ----------------------------------------------------------------


_STREAM_SENTINEL = object()


def _validate_team_inventories(
    body: TeamOptimizeRequest, index: VaultIndex
) -> None:
    """Reject parties with unknown characters or duplicates — the engine
    happily de-duplicates inventories internally, but a human asking
    for "Lune + Lune" almost certainly meant something else."""
    seen: set[str] = set()
    for i, inv in enumerate(body.inventories):
        if inv.character not in index.characters:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"member {i}: character {inv.character!r} not found in vault "
                    f"(known: {sorted(index.characters)})"
                ),
            )
        if inv.character in seen:
            raise HTTPException(
                status_code=400,
                detail=f"member {i}: character {inv.character!r} appears twice in the party",
            )
        seen.add(inv.character)


def _team_to_response(team: Any, inventories: list[Any]) -> TeamBuildResponse:
    return TeamBuildResponse(
        members=[
            TeamMemberResponse(
                inventory_index=m.inventory_index,
                build=_to_response(
                    idx + 1,
                    m.build,
                    pp_budget=inventories[m.inventory_index].pp_budget,
                    weapon_levels=inventories[m.inventory_index].weapon_levels,
                ),
            )
            for idx, m in enumerate(team.members)
        ],
        total_score=team.total_score,
    )


async def _team_event_stream(
    body: TeamOptimizeRequest,
    index: VaultIndex,
    options: EngineOptions,
) -> AsyncIterator[bytes]:
    events: queue.Queue[Any] = queue.Queue()

    def on_progress(phase: str, pct: float) -> None:
        events.put({"event": "progress", "phase": phase, "pct": pct})

    def runner() -> None:
        try:
            result = optimize_team(
                body.inventories, index, options, on_progress=on_progress
            )
            response = TeamOptimizeResponse(
                teams=[_team_to_response(t, body.inventories) for t in result.teams]
            )
            events.put({"event": "result", "data": response.model_dump(mode="json")})
        except Exception as exc:  # pragma: no cover — defensive surface
            log.exception("team optimize stream failed")
            events.put({"event": "error", "detail": str(exc)})
        finally:
            events.put(_STREAM_SENTINEL)

    threading.Thread(target=runner, daemon=True).start()

    loop = asyncio.get_running_loop()
    while True:
        item = await loop.run_in_executor(None, events.get)
        if item is _STREAM_SENTINEL:
            return
        yield (json.dumps(item) + "\n").encode("utf-8")


async def _optimize_event_stream(
    body: OptimizeRequest,
    index: VaultIndex,
    options: EngineOptions,
) -> AsyncIterator[bytes]:
    """Run ``optimize`` on a worker thread and forward progress + result
    events back through the response. We run the work on a thread (rather
    than awaiting an async optimize) because the engine is CPU-bound — an
    async loop would just block. The thread feeds a ``queue.Queue`` and
    this coroutine drains it via ``run_in_executor``."""
    events: queue.Queue[Any] = queue.Queue()

    def on_progress(phase: str, pct: float) -> None:
        events.put({"event": "progress", "phase": phase, "pct": pct})

    def runner() -> None:
        try:
            result = optimize(body.inventory, index, options, on_progress=on_progress)
            response = OptimizeResponse(
                builds=[
                    _to_response(
                        rank,
                        b,
                        pp_budget=body.inventory.pp_budget,
                        weapon_levels=body.inventory.weapon_levels,
                    )
                    for rank, b in enumerate(result.builds, start=1)
                ],
                aspirational=list(result.aspirational),
            )
            events.put({"event": "result", "data": response.model_dump(mode="json")})
        except Exception as exc:  # pragma: no cover — defensive surface
            log.exception("optimize stream failed")
            events.put({"event": "error", "detail": str(exc)})
        finally:
            events.put(_STREAM_SENTINEL)

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()

    loop = asyncio.get_running_loop()
    while True:
        item = await loop.run_in_executor(None, events.get)
        if item is _STREAM_SENTINEL:
            return
        yield (json.dumps(item) + "\n").encode("utf-8")


_KNOWN_TYPES: frozenset[str] = frozenset({"character", "picto", "weapon", "lumina", "skill"})


def _api_asset_path(vault_relative: str | None) -> str | None:
    """Turn ``_assets/Pictos/foo.png`` (as stored on the entry) into
    ``Pictos/foo.png`` (as served under ``/assets``)."""
    if not vault_relative:
        return None
    prefix = "_assets/"
    if vault_relative.startswith(prefix):
        return vault_relative[len(prefix) :]
    return vault_relative


def _project_items(index: VaultIndex, type: str, character: str | None) -> list[VaultItem]:
    type_low = type.lower()
    if type_low not in _KNOWN_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"unknown type {type!r}. Known: {sorted(_KNOWN_TYPES)}",
        )

    if type_low == "character":
        entries: list[VaultItem] = [
            VaultItem(slug=c.slug, name=c.name, image_path=_api_asset_path(c.image_path))
            for c in index.characters.values()
        ]
    elif type_low == "picto":
        entries = [
            VaultItem(
                slug=p.slug,
                name=p.name,
                category=p.category,
                pp_cost=p.lumina_points_cost,
                effect=p.effect,
                effect_structured=p.effect_structured,
                stats_granted=p.stats_granted,
                image_path=_api_asset_path(p.image_path),
            )
            for p in index.pictos.values()
        ]
    elif type_low == "lumina":
        entries = [
            VaultItem(
                slug=lu.slug,
                name=lu.name,
                category=lu.category,
                pp_cost=lu.pp_cost,
                effect=lu.effect,
                effect_structured=lu.effect_structured,
                image_path=_api_asset_path(lu.image_path),
            )
            for lu in index.luminas.values()
        ]
    elif type_low == "weapon":
        entries = [
            VaultItem(
                slug=w.slug,
                name=w.name,
                character=w.character,
                base_damage=w.base_damage,
                scaling_stat=w.scaling_stat,
                passives=w.passives,
                image_path=_api_asset_path(w.image_path),
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
                image_path=_api_asset_path(s.image_path),
            )
            for s in index.skills.values()
        ]

    if character is not None:
        char_low = character.lower()
        entries = [e for e in entries if (e.character or "").lower() == char_low]
    entries.sort(key=lambda e: e.name.lower())
    return entries


def _to_response(
    rank: int,
    r: RankedBuild,
    *,
    pp_budget: int = 0,
    weapon_levels: dict[str, int] | None = None,
) -> RankedBuildResponse:
    pp_used = sum(int(lu.pp_cost or 0) for lu in r.build.luminas)
    weapon_level = (weapon_levels or {}).get(r.build.weapon.slug)
    return RankedBuildResponse(
        rank=rank,
        total_score=r.total_score,
        loadout=BuildLoadout(
            character=r.build.character.slug,
            weapon=r.build.weapon.slug,
            weapon_level=weapon_level,
            pictos=[p.slug for p in r.build.pictos],
            luminas=[lu.slug for lu in r.build.luminas],
            skills_used=[s.slug for s in r.build.skills_used],
            pp_used=pp_used,
            pp_budget=pp_budget,
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
        deck_variants=[
            DeckVariantResponse(
                weapon=v.weapon,
                pictos=v.pictos,
                luminas=v.luminas,
                est_dps=v.est_dps,
                raw_dps=v.raw_dps,
            )
            for v in r.deck_variants
        ],
        archetype=r.archetype,
        rotation_trace=r.rotation_trace,
    )
