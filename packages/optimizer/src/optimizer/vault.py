"""Read the Obsidian vault into typed in-memory indices."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

import frontmatter
from pydantic import BaseModel

from optimizer.models import (
    CharacterItem,
    CuratedBuild,
    FormulaItem,
    LuminaItem,
    PictoItem,
    SkillItem,
    SynergyItem,
    WeaponItem,
)

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass(slots=True)
class VaultIndex:
    """Everything the optimizer needs, keyed for O(1) lookups."""

    characters: dict[str, CharacterItem] = field(default_factory=dict)
    pictos: dict[str, PictoItem] = field(default_factory=dict)
    weapons: dict[str, WeaponItem] = field(default_factory=dict)
    luminas: dict[str, LuminaItem] = field(default_factory=dict)
    skills: dict[str, SkillItem] = field(default_factory=dict)
    synergies: list[SynergyItem] = field(default_factory=list)
    formulas: dict[str, FormulaItem] = field(default_factory=dict)
    curated_builds: list[CuratedBuild] = field(default_factory=list)

    def weapons_for(self, character_slug: str) -> list[WeaponItem]:
        target = character_slug.lower()
        return [w for w in self.weapons.values() if (w.character or "").lower() == target]

    def skills_for(self, character_slug: str) -> list[SkillItem]:
        target = character_slug.lower()
        return [s for s in self.skills.values() if (s.character or "").lower() == target]


# --- loader -----------------------------------------------------------------


_FOLDER_TO_TYPE: dict[str, type[BaseModel]] = {
    "Characters": CharacterItem,
    "Pictos": PictoItem,
    "Weapons": WeaponItem,
    "Luminas": LuminaItem,
    "Skills": SkillItem,
    "Synergies": SynergyItem,
    "Formulas": FormulaItem,
    "Builds": CuratedBuild,
}


class VaultLoader:
    """Walk a vault directory and materialise every entry into the index."""

    def __init__(self, vault_dir: Path) -> None:
        self._vault = vault_dir

    def load(self) -> VaultIndex:
        index = VaultIndex()
        for folder, model_cls in _FOLDER_TO_TYPE.items():
            folder_path = self._vault / folder
            if not folder_path.is_dir():
                log.debug("vault: folder %s missing — skipping", folder)
                continue
            for md_path in sorted(folder_path.glob("*.md")):
                if md_path.name.startswith("_") or md_path.name.startswith("00_"):
                    continue
                item = self._parse(md_path, model_cls)
                if item is None:
                    continue
                self._register(index, folder, item)
        return index

    @staticmethod
    def _parse(path: Path, model_cls: type[T]) -> T | None:
        try:
            post = frontmatter.load(path)
        except Exception as exc:  # pragma: no cover — corruption is logged, skipped
            log.warning("vault: failed to parse %s: %r", path, exc)
            return None
        data: dict[str, Any] = dict(post.metadata)
        data.setdefault("slug", path.stem)
        data.setdefault("name", path.stem.replace("-", " ").title())
        data["body"] = post.content
        try:
            return model_cls.model_validate(data)
        except Exception as exc:  # pragma: no cover
            log.warning("vault: %s does not validate as %s: %r", path, model_cls.__name__, exc)
            return None

    @staticmethod
    def _register(index: VaultIndex, folder: str, item: BaseModel) -> None:
        if isinstance(item, CharacterItem):
            index.characters[item.slug] = item
        elif isinstance(item, PictoItem):
            index.pictos[item.slug] = item
        elif isinstance(item, WeaponItem):
            index.weapons[item.slug] = item
        elif isinstance(item, LuminaItem):
            index.luminas[item.slug] = item
        elif isinstance(item, SkillItem):
            index.skills[item.slug] = item
        elif isinstance(item, SynergyItem):
            index.synergies.append(item)
        elif isinstance(item, FormulaItem):
            index.formulas[item.slug] = item
        elif isinstance(item, CuratedBuild):
            index.curated_builds.append(item)
        else:  # pragma: no cover — exhaustive above
            log.warning("vault: unknown item type from folder %s", folder)
