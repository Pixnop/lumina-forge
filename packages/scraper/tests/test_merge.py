"""Merger contract: never lose information, record conflicts, union lists."""

from __future__ import annotations

from pathlib import Path

import frontmatter
import pytest
from scraper.merge import MergeOutcome, VaultMerger
from scraper.models import Picto


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    (tmp_path / "Pictos").mkdir()
    return tmp_path


def _load(path: Path) -> tuple[dict[str, object], str]:
    post = frontmatter.loads(path.read_text(encoding="utf-8"))
    return dict(post.metadata), post.content


def test_creates_when_missing(vault: Path) -> None:
    merger = VaultMerger(vault)
    picto = Picto(
        slug="demo",
        name="Demo",
        effect="do stuff",
        sources=["https://a.example/demo"],  # type: ignore[list-item]
    )

    result = merger.upsert(picto)

    assert result.outcome is MergeOutcome.CREATED
    assert result.path.exists()
    meta, body = _load(result.path)
    assert meta["name"] == "Demo"
    assert body.strip() == ""


def test_unchanged_when_same_data_resent(vault: Path) -> None:
    merger = VaultMerger(vault)
    picto = Picto(slug="demo", name="Demo", effect="do stuff", sources=["https://a.example/demo"])  # type: ignore[list-item]
    merger.upsert(picto)

    result = merger.upsert(picto)

    assert result.outcome is MergeOutcome.UNCHANGED


def test_scalar_conflict_is_recorded_not_overwritten(vault: Path) -> None:
    merger = VaultMerger(vault)
    merger.upsert(
        Picto(slug="demo", name="Demo", lumina_points_cost=10, sources=["https://a.example/demo"])  # type: ignore[list-item]
    )

    result = merger.upsert(
        Picto(slug="demo", name="Demo", lumina_points_cost=12, sources=["https://b.example/demo"])  # type: ignore[list-item]
    )

    assert result.outcome is MergeOutcome.UPDATED
    meta, _ = _load(result.path)
    # original scalar preserved as the "truth" surface
    assert meta["lumina_points_cost"] == 10
    # but both values are visible in conflicts
    conflicts = meta["conflicts"]
    assert isinstance(conflicts, dict)
    entry = conflicts["lumina_points_cost"]
    assert isinstance(entry, list)
    values = {item["value"] for item in entry}  # type: ignore[index]
    assert values == {10, 12}


def test_list_union_preserves_order_and_dedupes(vault: Path) -> None:
    merger = VaultMerger(vault)
    merger.upsert(
        Picto(
            slug="demo",
            name="Demo",
            stats_granted={"Speed": 0, "Health": 0},
            sources=["https://a.example/demo"],  # type: ignore[list-item]
        )
    )

    result = merger.upsert(
        Picto(
            slug="demo",
            name="Demo",
            stats_granted={"Health": 0, "Agility": 0},
            sources=["https://b.example/demo"],  # type: ignore[list-item]
        )
    )

    meta, _ = _load(result.path)
    # dicts with overlapping keys should merge at the key level, not conflict
    assert meta["stats_granted"] == {"Speed": 0, "Health": 0, "Agility": 0}


def test_sources_are_appended_without_duplicates(vault: Path) -> None:
    merger = VaultMerger(vault)
    merger.upsert(Picto(slug="demo", name="Demo", sources=["https://a.example/demo"]))  # type: ignore[list-item]
    # same URL — must not produce a change
    merger.upsert(Picto(slug="demo", name="Demo", sources=["https://a.example/demo"]))  # type: ignore[list-item]
    result = merger.upsert(Picto(slug="demo", name="Demo", sources=["https://b.example/demo"]))  # type: ignore[list-item]

    meta, _ = _load(result.path)
    assert meta["sources"] == [
        "https://a.example/demo",
        "https://b.example/demo",
    ]


def test_body_gets_per_source_notes_section(vault: Path) -> None:
    merger = VaultMerger(vault)
    merger.upsert(Picto(slug="demo", name="Demo", body="original insight", sources=["https://a.example/demo"]))  # type: ignore[list-item]
    result = merger.upsert(
        Picto(slug="demo", name="Demo", body="alternative take", sources=["https://b.example/demo"])  # type: ignore[list-item]
    )

    _, body = _load(result.path)
    assert "original insight" in body
    assert "alternative take" in body
    assert "## Notes — https://b.example/demo" in body


def test_dry_run_does_not_write(vault: Path) -> None:
    merger = VaultMerger(vault, dry_run=True)
    result = merger.upsert(Picto(slug="demo", name="Demo"))
    assert result.outcome is MergeOutcome.CREATED
    assert not result.path.exists()
