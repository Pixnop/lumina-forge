"""Bundle lumina-forge-api into a standalone .exe for Tauri to ship as a sidecar.

Run from the repo root:

    uv run python scripts/build_api_exe.py

Output lands at ``app/src-tauri/binaries/lumina-forge-api-<target-triple>.exe``,
the exact path Tauri expects when ``bundle.externalBin`` lists
``binaries/lumina-forge-api``.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TAURI_DIR = REPO_ROOT / "app" / "src-tauri"
OUTPUT_DIR = TAURI_DIR / "binaries"
ENTRY_SCRIPT = REPO_ROOT / "scripts" / "_api_entry.py"


def target_triple() -> str:
    """Return the rustc target triple Tauri expects in the sidecar filename."""
    try:
        raw = subprocess.check_output(["rustc", "-vV"], text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Fallback mapping for when rustc is not in PATH.
        system = platform.system().lower()
        machine = platform.machine().lower()
        if system == "windows":
            if machine in ("amd64", "x86_64"):
                return "x86_64-pc-windows-gnu"
            return f"{machine}-pc-windows-gnu"
        if system == "darwin":
            return "aarch64-apple-darwin" if machine == "arm64" else "x86_64-apple-darwin"
        return "x86_64-unknown-linux-gnu"
    for line in raw.splitlines():
        if line.startswith("host:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("rustc printed no host line — can't infer target triple")


def main() -> int:
    triple = target_triple()
    exe_name = f"lumina-forge-api-{triple}"
    print(f"[build_api_exe] target triple: {triple}")
    print(f"[build_api_exe] output: {OUTPUT_DIR / exe_name}.exe")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    work_dir = TAURI_DIR / ".pyinstaller-work"
    dist_dir = TAURI_DIR / ".pyinstaller-dist"

    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconfirm",
        "--name", exe_name,
        "--workpath", str(work_dir),
        "--distpath", str(dist_dir),
        "--specpath", str(work_dir),
        # uvicorn's entry resolution uses importlib.metadata — explicit collect keeps it happy
        "--collect-submodules", "uvicorn",
        "--collect-submodules", "fastapi",
        "--collect-submodules", "optimizer",
        "--hidden-import", "optimizer.api.main",
        str(ENTRY_SCRIPT),
    ]
    env = os.environ.copy()
    print(f"[build_api_exe] running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print("[build_api_exe] pyinstaller failed", file=sys.stderr)
        return result.returncode

    built = dist_dir / f"{exe_name}.exe"
    target = OUTPUT_DIR / f"{exe_name}.exe"
    if not built.exists():
        print(f"[build_api_exe] expected {built} but it was not produced", file=sys.stderr)
        return 1
    shutil.copy2(built, target)
    print(f"[build_api_exe] copied to {target}")

    # Tauri's MSI bundler on Windows hosts always looks up sidecars under
    # the msvc triple, regardless of the rustc toolchain in use. Drop a
    # twin copy so the bundle step finds it.
    if "windows" in triple and triple.endswith("gnu"):
        twin = triple.replace("-gnu", "-msvc")
        twin_target = OUTPUT_DIR / f"lumina-forge-api-{twin}.exe"
        shutil.copy2(built, twin_target)
        print(f"[build_api_exe] also copied to {twin_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
