"""PyInstaller entry-point for the bundled API.

This is what the compiled ``lumina-forge-api-<triple>.exe`` runs. We resolve
the vault directory relative to the bundle so the sidecar works regardless
of where Tauri drops the .exe at install time, and we start a watchdog
thread that kills this process when the Tauri parent dies (including after
force-kill via Task Manager, where no graceful signal reaches us).
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from pathlib import Path


def _bundled_vault_dir() -> Path:
    """Look for ``vault/`` next to the executable (PyInstaller one-file layout).

    When the sidecar is launched by Tauri, resources live alongside the .exe.
    We fall back to the current working directory so dev mode still works
    when you run the built .exe from the repo root.
    """
    exe_dir = Path(sys.executable).resolve().parent
    for candidate in (exe_dir / "vault", Path.cwd() / "vault"):
        if candidate.is_dir():
            return candidate
    # Last resort: whatever the CLI default is — surfaces a helpful error later.
    return Path.cwd() / "vault"


def _parent_is_alive(pid: int) -> bool:
    """Windows-friendly liveness probe.

    On Windows, ``os.kill(pid, 0)`` may raise ``PermissionError`` for
    processes we have no signal rights on — that still means the PID is
    live. Only ``ProcessLookupError`` (ESRCH) is a reliable "dead" signal.
    """
    if sys.platform == "win32":
        import ctypes  # noqa: PLC0415 — platform-gated

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
        )
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            return exit_code.value == STILL_ACTIVE
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _watch_parent(pid: int, poll_seconds: float = 2.0) -> None:
    """Exit the sidecar if the Tauri parent dies. Runs in a daemon thread."""
    while True:
        time.sleep(poll_seconds)
        if not _parent_is_alive(pid):
            # Hard exit — no graceful shutdown needed since the UI is already gone.
            os._exit(0)


def _peel_parent_pid() -> int | None:
    """Remove ``--parent-pid <pid>`` from ``sys.argv`` in place, return it.

    We peel it ourselves rather than letting typer reject the flag, because
    the rest of the CLI is owned by ``optimizer.api.main`` and we don't want
    to couple the watchdog flag to its schema.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--parent-pid", type=int, default=None)
    known, remaining = parser.parse_known_args(sys.argv[1:])
    sys.argv[1:] = remaining
    return known.parent_pid


def main() -> None:
    parent_pid = _peel_parent_pid()
    if parent_pid is not None:
        threading.Thread(target=_watch_parent, args=(parent_pid,), daemon=True).start()

    os.chdir(_bundled_vault_dir().parent)
    from optimizer.api.main import main as api_main  # noqa: PLC0415 — lazy import for speed
    api_main()


if __name__ == "__main__":
    main()
