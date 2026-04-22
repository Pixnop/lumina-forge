"""Download images referenced by vault entries into ``vault/_assets/``.

The scraper parsers extract ``image_url`` from each index row. This
downloader turns that remote URL into a local file, then writes the
relative path back onto the vault entry's frontmatter under
``image_path``.

Idempotent: re-running skips files that already exist on disk. Failures
are logged and counted but don't abort the pass.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import frontmatter
import httpx

log = logging.getLogger(__name__)

USER_AGENT = "lumina-forge/0.5 (+https://github.com/Pixnop/lumina-forge)"

_FOLDER_NAMES = ("Pictos", "Luminas", "Weapons", "Skills", "Characters")
_ASSETS_DIR_NAME = "_assets"


@dataclass(slots=True)
class AssetsReport:
    downloaded: int = 0
    already_cached: int = 0
    missing_url: int = 0
    errors: list[str] = field(default_factory=list)


def download_assets(vault_dir: Path, *, timeout: float = 30.0) -> AssetsReport:
    """Walk the vault, fetch any missing images, update frontmatters."""
    report = AssetsReport()
    assets_root = vault_dir / _ASSETS_DIR_NAME
    assets_root.mkdir(exist_ok=True)

    with httpx.Client(
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    ) as client:
        for folder in _FOLDER_NAMES:
            folder_path = vault_dir / folder
            if not folder_path.is_dir():
                continue
            target_dir = assets_root / folder
            target_dir.mkdir(exist_ok=True)
            for md_path in sorted(folder_path.glob("*.md")):
                if md_path.name.startswith("_"):
                    continue
                _process_entry(md_path, target_dir, folder, client, report)
    return report


# --- internals --------------------------------------------------------------


def _process_entry(
    md_path: Path,
    target_dir: Path,
    folder: str,
    client: httpx.Client,
    report: AssetsReport,
) -> None:
    try:
        post = frontmatter.load(md_path)
    except Exception as exc:  # pragma: no cover
        report.errors.append(f"read {md_path.name}: {exc!r}")
        return
    image_url = post.metadata.get("image_url")
    if not isinstance(image_url, str) or not image_url:
        report.missing_url += 1
        return

    ext = _infer_extension(image_url)
    target = target_dir / f"{md_path.stem}{ext}"
    rel_path = f"{_ASSETS_DIR_NAME}/{folder}/{target.name}"

    if target.exists():
        report.already_cached += 1
        # Still make sure image_path is recorded on the frontmatter.
        if post.metadata.get("image_path") != rel_path:
            post.metadata["image_path"] = rel_path
            _write_frontmatter(md_path, post)
        return

    try:
        response = client.get(image_url)
        response.raise_for_status()
    except Exception as exc:
        report.errors.append(f"fetch {md_path.stem}: {exc!r}")
        return

    target.write_bytes(response.content)
    post.metadata["image_path"] = rel_path
    _write_frontmatter(md_path, post)
    report.downloaded += 1
    log.debug("downloaded %s (%d bytes)", rel_path, len(response.content))


def _infer_extension(url: str) -> str:
    path = urlparse(url).path.lower()
    # Strip any query/hash noise then match the final dot-extension.
    match = re.search(r"\.(png|jpe?g|gif|webp|svg)$", path)
    if match is None:
        return ".png"
    ext = match.group(1).lower()
    return f".{'jpg' if ext == 'jpeg' else ext}"


def _write_frontmatter(path: Path, post: frontmatter.Post) -> None:
    """Serialise with a stable YAML order so diffs stay minimal."""
    import yaml

    yaml_text = yaml.safe_dump(
        dict(post.metadata), sort_keys=True, allow_unicode=True
    )
    content = f"---\n{yaml_text}---\n\n{post.content}\n"
    path.write_text(content, encoding="utf-8")
