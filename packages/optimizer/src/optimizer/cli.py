"""``optimizer`` CLI: JSON inventory in, top-N builds out."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from optimizer.engine import EngineOptions, OptimizeResult, optimize
from optimizer.models import AspirationalBuild, Inventory, Mode, RankedBuild
from optimizer.vault import VaultLoader

app = typer.Typer(add_completion=False, help="Rank Expedition 33 builds from an inventory JSON.")
console = Console()


@app.callback(invoke_without_command=True)
def run(
    inventory: Annotated[
        Path,
        typer.Option("--inventory", "-i", help="Path to a JSON inventory."),
    ],
    vault_dir: Annotated[Path, typer.Option("--vault-dir", help="Vault root.")] = Path("vault"),
    top: Annotated[int, typer.Option("--top", "-n", min=1, help="How many builds to return.")] = 5,
    mode: Annotated[Mode, typer.Option("--mode", help="Ranking mode.")] = "dps",
    weight_utility: Annotated[
        float | None,
        typer.Option("--weight-utility", help="Explicit utility weight (0.0 = pure DPS)."),
    ] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="DEBUG logging.")] = False,
) -> None:
    _configure_logging(verbose)

    inv = _load_inventory(inventory)
    index = VaultLoader(vault_dir.resolve()).load()
    if inv.character not in index.characters:
        typer.echo(
            f"character {inv.character!r} not found in vault at {vault_dir} "
            f"(known: {sorted(index.characters)})",
            err=True,
        )
        raise typer.Exit(code=2)

    options = EngineOptions(top_k=top, mode=mode, weight_utility=weight_utility)
    result = optimize(inv, index, options)

    if not result.builds:
        console.print(
            Panel(
                "No build could be assembled from this inventory.\n"
                "Check that you have at least one compatible weapon and ≥ 3 pictos.",
                title="[bold red]No builds[/]",
            )
        )
        raise typer.Exit(code=1)

    _render(result, inv, options)


# --- helpers ----------------------------------------------------------------


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )


def _load_inventory(path: Path) -> Inventory:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        typer.echo(f"inventory file not found: {path}", err=True)
        raise typer.Exit(code=2) from None
    except json.JSONDecodeError as exc:
        typer.echo(f"inventory JSON is invalid: {exc}", err=True)
        raise typer.Exit(code=2) from None
    try:
        return Inventory.model_validate(data)
    except Exception as exc:  # pydantic ValidationError, etc.
        typer.echo(f"inventory does not match schema: {exc}", err=True)
        raise typer.Exit(code=2) from None


def _render(result: OptimizeResult, inventory: Inventory, options: EngineOptions) -> None:
    ranked = result.builds
    weight = options.resolved_utility_weight()
    console.rule(
        f"[bold]optimizer[/] — character=[cyan]{inventory.character}[/] "
        f"mode=[yellow]{options.mode}[/] utility_weight=[magenta]{weight:.2f}[/]"
    )

    table = Table(title=f"Top {len(ranked)} builds", header_style="bold")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Archetype")
    table.add_column("Weapon")
    table.add_column("Pictos")
    table.add_column("Luminas", overflow="fold")
    table.add_column("DPS", justify="right")
    table.add_column("Utility", justify="right")
    table.add_column("Total", justify="right", style="bold cyan")

    for idx, r in enumerate(ranked, start=1):
        pictos = "\n".join(p.name for p in r.build.pictos)
        luminas = ", ".join(lu.name for lu in r.build.luminas) or "—"
        archetype_cell = _archetype_cell(r)
        table.add_row(
            str(idx),
            archetype_cell,
            r.build.weapon.name,
            pictos,
            luminas,
            f"{r.damage.est_dps:.0f}",
            f"{r.utility.score_0_1:.2f}",
            f"{r.total_score:.0f}",
        )
    console.print(table)

    for idx, r in enumerate(ranked, start=1):
        reasons = "\n".join(f"• {line}" for line in r.why)
        rotation = "\n".join(f"  {line}" for line in r.rotation_hint)
        alt_block = ""
        if r.weapon_alternatives:
            alts = "\n".join(
                f"  • [cyan]{a.weapon}[/] — raw {a.raw_dps:.0f}"
                + (" [yellow](capped)[/]" if a.est_dps < a.raw_dps else "")
                for a in r.weapon_alternatives
            )
            alt_block = f"\n\n[bold]Also works with:[/]\n{alts}"
        title = f"#{idx} — {r.build.weapon.name}"
        if r.archetype is not None:
            tag = "exact" if r.archetype.confidence == "exact" else "variant"
            title += f"  [green]▸ {r.archetype.name} ({r.archetype.dps_tier} · {tag})[/]"
        console.print(
            Panel(
                f"{reasons}\n\n[bold]Rotation:[/]\n{rotation}{alt_block}",
                title=title,
                border_style="cyan",
            )
        )

    if result.aspirational:
        _render_aspirational(result.aspirational)


def _archetype_cell(r: RankedBuild) -> str:
    if r.archetype is None:
        return "[dim]—[/]"
    tier = r.archetype.dps_tier or "?"
    tag = "" if r.archetype.confidence == "exact" else "\n[dim](variant)[/]"
    return f"[green]{r.archetype.name}[/]\n[yellow]{tier}-tier[/]{tag}"


def _render_aspirational(aspirational: list[AspirationalBuild]) -> None:
    lines: list[str] = []
    for entry in aspirational:
        missing: list[str] = []
        if entry.missing_weapon:
            missing.append(f"weapon [cyan]{entry.missing_weapon}[/]")
        if entry.missing_pictos:
            missing.append("picto(s) " + ", ".join(f"[cyan]{p}[/]" for p in entry.missing_pictos))
        if entry.missing_luminas:
            missing.append(
                "lumina(s) " + ", ".join(f"[cyan]{lu}[/]" for lu in entry.missing_luminas)
            )
        if entry.missing_skills:
            missing.append(
                "skill(s) " + ", ".join(f"[cyan]{s}[/]" for s in entry.missing_skills)
            )
        lines.append(
            f"[bold]{entry.name}[/] [yellow]({entry.dps_tier})[/] "
            f"— you're missing: {'; '.join(missing)}"
        )
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold]Close to:[/] curated archetypes you can almost run",
            border_style="yellow",
        )
    )


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
