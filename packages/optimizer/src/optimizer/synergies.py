"""Match a Build against the synergies stored in the vault.

Synergies live under ``vault/Synergies/*.md`` and document validated
cross-component combos (picto + skill + lumina → +X damage). Phase 2 hasn't
populated them yet — when it does, each entry describes the required
components plus a ``score_bonus`` multiplier.

For now this module provides the hook: the loader still returns ``[]`` from
an empty ``Synergies/`` folder, and :meth:`SynergyMatcher.matches` is ready
to check any entry that lands there.
"""

from __future__ import annotations

from dataclasses import dataclass

from optimizer.models import Build, SynergyItem


@dataclass(frozen=True, slots=True)
class SynergyMatcher:
    """Check which of the vault's synergies apply to a given build."""

    synergies: tuple[SynergyItem, ...]

    def matches(self, build: Build) -> list[SynergyItem]:
        return [s for s in self.synergies if self._build_satisfies(build, s)]

    def multiplier(self, matches: list[SynergyItem]) -> float:
        """Combine matching synergies into a single multiplicative factor."""
        return 1.0 + sum(s.score_bonus for s in matches)

    # --- component matching rules ----------------------------------------

    @staticmethod
    def _build_satisfies(build: Build, synergy: SynergyItem) -> bool:
        components = synergy.components or {}
        required_pictos = _as_slug_list(components.get("pictos"))
        required_luminas = _as_slug_list(components.get("luminas"))
        required_skills = _as_slug_list(components.get("skills"))
        required_weapons = _as_slug_list(components.get("weapons"))

        build_pictos = {p.slug for p in build.pictos}
        build_luminas = {lu.slug for lu in build.luminas}
        build_skills = {s.slug for s in build.skills_used}

        if required_pictos and not set(required_pictos).issubset(build_pictos):
            return False
        if required_luminas and not set(required_luminas).issubset(build_luminas):
            return False
        if required_skills and not set(required_skills).issubset(build_skills):
            return False
        return not (required_weapons and build.weapon.slug not in required_weapons)


def _as_slug_list(raw: object) -> list[str]:
    """Accept either ``["slug", ...]`` or ``["Folder/slug", ...]`` shapes.

    Synergy authors often write component refs the Obsidian way
    (``Skills/overcharge``) — strip the folder prefix to get bare slugs.
    """
    if not isinstance(raw, list):
        return []
    result: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        slug = item.split("/")[-1].strip()
        if slug:
            result.append(slug)
    return result
