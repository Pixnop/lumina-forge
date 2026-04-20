"""Orchestrator: discover → fetch → parse → merge → report."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from scraper.config import FetcherConfig, Paths
from scraper.fetch import HttpFetcher, RobotsDisallowedError
from scraper.merge import MergeOutcome, VaultMerger
from scraper.models import ScrapeReport
from scraper.sources import get_adapter
from scraper.sources.base import EntryType

log = logging.getLogger(__name__)


@dataclass(slots=True)
class ScrapeOptions:
    source_id: str
    entry_types: list[EntryType]
    limit: int | None = None
    refresh: bool = False
    dry_run: bool = False


def scrape(paths: Paths, options: ScrapeOptions) -> ScrapeReport:
    """Run one full scrape pass and return the final :class:`ScrapeReport`."""
    report = ScrapeReport(source_id=options.source_id)
    adapter_cls = get_adapter(options.source_id)
    adapter = adapter_cls()
    merger = VaultMerger(paths.vault, dry_run=options.dry_run)

    fetcher_config = FetcherConfig(refresh=options.refresh)
    with HttpFetcher(paths.cache, config=fetcher_config) as fetcher:
        produced = 0
        for entry_type, url in adapter.discover(fetcher, options.entry_types):
            if options.limit is not None and produced >= options.limit:
                break
            try:
                page, from_cache = fetcher.get(url, source_id=options.source_id)
            except RobotsDisallowedError as exc:
                _record_error(report, f"robots: {exc}")
                continue
            except Exception as exc:
                _record_error(report, f"fetch {url}: {exc!r}")
                continue

            report.pages_fetched += 0 if from_cache else 1
            report.pages_from_cache += 1 if from_cache else 0

            try:
                entries = list(adapter.parse(entry_type, page))
            except Exception as exc:
                _record_error(report, f"parse {url}: {exc!r}")
                continue

            for entry in entries:
                if options.limit is not None and produced >= options.limit:
                    break
                produced += 1
                try:
                    result = merger.upsert(entry)
                except Exception as exc:
                    _record_error(report, f"merge {entry.slug}: {exc!r}")
                    continue
                _tally(report, result.outcome)

    report.finished_at = datetime.now()
    _persist_report(paths.cache, report)
    return report


def _tally(report: ScrapeReport, outcome: MergeOutcome) -> None:
    if outcome is MergeOutcome.CREATED:
        report.entries_created += 1
    elif outcome is MergeOutcome.UPDATED:
        report.entries_updated += 1
    else:
        report.entries_unchanged += 1


def _record_error(report: ScrapeReport, msg: str) -> None:
    log.warning(msg)
    report.errors.append(msg)


def _persist_report(cache_dir: Path, report: ScrapeReport) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{report.source_id}-report.json"
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
