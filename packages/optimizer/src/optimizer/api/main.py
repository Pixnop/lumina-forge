"""``lumina-forge-api`` CLI — thin wrapper around uvicorn."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from optimizer.api.app import create_app

cli = typer.Typer(add_completion=False, help="Run the lumina-forge local API.")


@cli.callback(invoke_without_command=True)
def run(
    host: Annotated[str, typer.Option("--host", help="Bind address.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Bind port.")] = 31733,
    vault_dir: Annotated[
        Path, typer.Option("--vault-dir", help="Vault root to serve from.")
    ] = Path("vault"),
    reload: Annotated[bool, typer.Option("--reload", help="Auto-reload on file changes.")] = False,
) -> None:
    app = create_app(vault_dir=vault_dir)
    uvicorn.run(app, host=host, port=port, reload=reload)


def main() -> None:  # pragma: no cover
    cli()


if __name__ == "__main__":  # pragma: no cover
    main()
