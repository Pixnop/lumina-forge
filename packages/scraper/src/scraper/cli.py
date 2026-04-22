"""``scraper`` CLI entry point."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from scraper.assets import AssetsReport, download_assets
from scraper.config import Paths
from scraper.models import ScrapeReport
from scraper.pipeline import ScrapeOptions, scrape
from scraper.sources import ADAPTERS
from scraper.sources.base import EntryType

app = typer.Typer(add_completion=False, help="Scrape Expedition 33 guides into the Obsidian vault.")
console = Console()

ALL_TYPES: list[EntryType] = ["character", "picto", "weapon", "lumina", "skill"]


@app.callback(invoke_without_command=True)
def run(
    source: Annotated[
        str,
        typer.Option("--source", "-s", help="Source adapter to run."),
    ] = "fextralife",
    types: Annotated[
        list[str] | None,
        typer.Option(
            "--type",
            "-t",
            help="Entry types to scrape. Omit to scrape all.",
        ),
    ] = None,
    refresh: Annotated[
        bool, typer.Option("--refresh", help="Ignore cache, re-fetch.")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Parse but don't write vault.")
    ] = False,
    limit: Annotated[
        int | None, typer.Option("--limit", help="Stop after N entries (debugging).")
    ] = None,
    vault_dir: Annotated[Path, typer.Option("--vault-dir", help="Vault root.")] = Path("vault"),
    cache_dir: Annotated[Path, typer.Option("--cache-dir", help="Cache root.")] = Path("cache"),
    skip_assets: Annotated[
        bool,
        typer.Option(
            "--skip-assets", help="Don't download images referenced by vault entries."
        ),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="DEBUG logging.")] = False,
) -> None:
    _configure_logging(verbose)

    if source not in ADAPTERS:
        known = ", ".join(sorted(ADAPTERS))
        typer.echo(f"unknown source {source!r}. Known: {known}", err=True)
        raise typer.Exit(code=2)

    entry_types: list[EntryType] = _validate_types(types)
    paths = Paths(vault=vault_dir.resolve(), cache=cache_dir.resolve())
    options = ScrapeOptions(
        source_id=source,
        entry_types=entry_types,
        limit=limit,
        refresh=refresh,
        dry_run=dry_run,
    )

    console.rule(f"[bold]scraper[/] — source=[cyan]{source}[/] dry_run=[yellow]{dry_run}[/]")
    report = scrape(paths, options)
    _print_report(report)

    if not dry_run and not skip_assets:
        console.rule("[bold]assets[/]")
        assets_report = download_assets(paths.vault)
        _print_assets_report(assets_report)

    if report.errors:
        raise typer.Exit(code=1)


# --- helpers ----------------------------------------------------------------


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )


def _validate_types(types: list[str] | None) -> list[EntryType]:
    if not types:
        return list(ALL_TYPES)
    invalid = set(types) - set(ALL_TYPES)
    if invalid:
        typer.echo(f"unknown entry types: {sorted(invalid)}. Known: {ALL_TYPES}", err=True)
        raise typer.Exit(code=2)
    return [t for t in ALL_TYPES if t in types]  # preserve canonical order


def _print_report(report: ScrapeReport) -> None:
    table = Table(title=f"Scrape report — {report.source_id}", show_header=False)
    table.add_column(style="bold cyan")
    table.add_column()
    table.add_row("pages fetched", str(report.pages_fetched))
    table.add_row("pages from cache", str(report.pages_from_cache))
    table.add_row("entries created", str(report.entries_created))
    table.add_row("entries updated", str(report.entries_updated))
    table.add_row("entries unchanged", str(report.entries_unchanged))
    table.add_row("errors", str(len(report.errors)))
    if report.finished_at and report.started_at:
        duration = (report.finished_at - report.started_at).total_seconds()
        table.add_row("duration (s)", f"{duration:.1f}")
    console.print(table)
    if report.errors:
        console.print("[bold red]Errors:[/]")
        for err in report.errors[:10]:
            console.print(f"  - {err}")
        if len(report.errors) > 10:
            console.print(f"  … {len(report.errors) - 10} more")


def _print_assets_report(report: AssetsReport) -> None:
    table = Table(title="Asset download", show_header=False)
    table.add_column(style="bold cyan")
    table.add_column()
    table.add_row("downloaded", str(report.downloaded))
    table.add_row("already cached", str(report.already_cached))
    table.add_row("no image_url", str(report.missing_url))
    table.add_row("errors", str(len(report.errors)))
    console.print(table)
    if report.errors:
        console.print("[bold yellow]Asset errors:[/]")
        for err in report.errors[:5]:
            console.print(f"  - {err}")
        if len(report.errors) > 5:
            console.print(f"  … {len(report.errors) - 5} more")


def main() -> None:  # pragma: no cover - thin shim for entry point
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
