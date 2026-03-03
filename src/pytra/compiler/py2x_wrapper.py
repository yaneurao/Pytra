"""Compatibility helper to run py2x with fixed target from legacy py2*.py CLIs."""

from __future__ import annotations

from pytra.std import sys

from py2x import main as py2x_main


def run_py2x_for_target(target: str, argv_override: list[str] | None = None) -> int:
    old_argv = sys.argv if isinstance(sys.argv, list) else []
    if isinstance(argv_override, list):
        forwarded = list(argv_override)
    else:
        forwarded = old_argv[1:] if isinstance(old_argv, list) and len(old_argv) >= 1 else []
    new_argv = ["py2x.py"] + forwarded + ["--target", target]
    sys.argv = new_argv
    try:
        rc = py2x_main()
        if isinstance(rc, int):
            return rc
        return 0
    finally:
        sys.argv = old_argv
