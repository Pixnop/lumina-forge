"""Write ``VaultEntry`` objects to the Obsidian vault, merging with existing notes."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import frontmatter
import yaml

from scraper.models import VaultEntry

log = logging.getLogger(__name__)


class MergeOutcome(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(slots=True)
class MergeResult:
    outcome: MergeOutcome
    path: Path


class VaultMerger:
    """Upsert a VaultEntry into ``vault/<Folder>/<slug>.md``.

    Rules when a note already exists for the same slug:

    - scalars that disagree go under ``conflicts.<field>`` as a list of
      ``{value, source}`` dicts, preserving each source's position;
    - list fields are unioned while preserving insertion order;
    - ``sources`` is deduplicated by URL and appended to;
    - the body gets a ``## Notes — <source>`` section appended per new source.

    We never silently overwrite a scalar. The merger is pure data — the
    orchestrator handles progress reporting.
    """

    def __init__(self, vault_dir: Path, *, dry_run: bool = False) -> None:
        self._vault = vault_dir
        self._dry_run = dry_run

    def upsert(self, entry: VaultEntry) -> MergeResult:
        target = self._target_path(entry)
        new_data = entry.frontmatter()
        new_body = entry.body

        if not target.exists():
            if not self._dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                self._write(target, new_data, new_body)
            return MergeResult(MergeOutcome.CREATED, target)

        existing = frontmatter.loads(target.read_text(encoding="utf-8"))
        merged_meta, changed_meta = _merge_frontmatter(dict(existing.metadata), new_data)
        merged_body, changed_body = _merge_body(existing.content, new_body, entry.sources)

        if not (changed_meta or changed_body):
            return MergeResult(MergeOutcome.UNCHANGED, target)

        if not self._dry_run:
            self._write(target, merged_meta, merged_body)
        return MergeResult(MergeOutcome.UPDATED, target)

    def _target_path(self, entry: VaultEntry) -> Path:
        return self._vault / entry.folder / f"{entry.slug}.md"

    @staticmethod
    def _write(target: Path, meta: dict[str, Any], body: str) -> None:
        post = frontmatter.Post(body, **meta)
        # python-frontmatter.dumps uses yaml internally; we route through PyYAML
        # directly so we can force a deterministic ordering and sane defaults.
        yaml_text = yaml.safe_dump(
            meta,
            sort_keys=True,
            allow_unicode=True,
            default_flow_style=False,
        )
        content = f"---\n{yaml_text}---\n\n{body.lstrip()}\n"
        target.write_text(content, encoding="utf-8")
        del post  # retain the import for linting tools — we keep Post available for future features


# --- pure helpers (no I/O) --------------------------------------------------


_SOURCE_KEY = "sources"
_CONFLICTS_KEY = "conflicts"


def _merge_frontmatter(
    existing: dict[str, Any], incoming: dict[str, Any]
) -> tuple[dict[str, Any], bool]:
    """Return (merged, changed). See class docstring for the merge rules."""
    merged = dict(existing)
    changed = False
    new_source = _primary_source(incoming)

    for key, new_value in incoming.items():
        if key == _CONFLICTS_KEY:
            continue
        if key == _SOURCE_KEY:
            old_sources = list(existing.get(_SOURCE_KEY, []))
            merged_sources = _union_preserving_order(old_sources, new_value)
            if merged_sources != old_sources:
                merged[_SOURCE_KEY] = merged_sources
                changed = True
            continue
        if key not in existing:
            merged[key] = new_value
            changed = True
            continue
        old_value = existing[key]
        if old_value == new_value:
            continue
        if isinstance(old_value, list) and isinstance(new_value, list):
            unioned = _union_preserving_order(old_value, new_value)
            if unioned != old_value:
                merged[key] = unioned
                changed = True
            continue
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            merged_dict, dict_changed = _merge_dict(old_value, new_value, key, new_source, merged)
            if dict_changed:
                merged[key] = merged_dict
                changed = True
            continue
        # Scalar conflict: record both values.
        merged = _record_conflict(merged, key, old_value, new_value, new_source)
        changed = True
    return merged, changed


def _merge_dict(
    old: dict[str, Any],
    new: dict[str, Any],
    parent_key: str,
    new_source: str | None,
    merged_parent: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Merge two dicts key by key. Overlapping keys with differing scalars go
    to the parent's ``conflicts.<parent_key>.<inner_key>`` entry."""
    result = dict(old)
    changed = False
    for inner_key, new_val in new.items():
        if inner_key not in result:
            result[inner_key] = new_val
            changed = True
            continue
        if result[inner_key] == new_val:
            continue
        # nested conflict — record under the parent_key
        conflicts = dict(merged_parent.get(_CONFLICTS_KEY, {}))
        bucket = dict(conflicts.get(parent_key, {}))
        entry = bucket.get(inner_key, [{"value": result[inner_key], "source": None}])
        candidate = {"value": new_val, "source": new_source}
        if candidate not in entry:
            entry.append(candidate)
        bucket[inner_key] = entry
        conflicts[parent_key] = bucket
        merged_parent[_CONFLICTS_KEY] = conflicts
        changed = True
    return result, changed


def _primary_source(data: dict[str, Any]) -> str | None:
    sources = data.get(_SOURCE_KEY) or []
    return sources[0] if sources else None


def _union_preserving_order(old: list[Any], new: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for item in [*old, *new]:
        key = _hashable(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _hashable(value: Any) -> Any:
    """Best-effort hash key for dedupe purposes."""
    if isinstance(value, dict):
        return tuple(sorted(value.items()))
    if isinstance(value, list):
        return tuple(_hashable(v) for v in value)
    return value


def _record_conflict(
    merged: dict[str, Any],
    key: str,
    old_value: Any,
    new_value: Any,
    new_source: str | None,
) -> dict[str, Any]:
    merged = dict(merged)
    conflicts = dict(merged.get(_CONFLICTS_KEY, {}))
    existing_entry = conflicts.get(key)
    if existing_entry is None:
        # Attribute the old value to the first existing source if any.
        old_source = _primary_source(merged)
        existing_entry = [{"value": old_value, "source": old_source}]
    candidate = {"value": new_value, "source": new_source}
    if candidate not in existing_entry:
        existing_entry.append(candidate)
    conflicts[key] = existing_entry
    merged[_CONFLICTS_KEY] = conflicts
    # Keep the scalar field as the first-seen value — the conflicts block has truth.
    return merged


def _merge_body(existing: str, incoming: str, sources: list[Any]) -> tuple[str, bool]:
    incoming = incoming.strip()
    if not incoming:
        return existing, False
    if incoming in existing:
        return existing, False
    source = str(sources[0]) if sources else "unknown-source"
    marker = f"## Notes — {source}"
    if marker in existing:
        return existing, False
    suffix = f"\n\n{marker}\n\n{incoming}\n"
    return existing.rstrip() + suffix, True
