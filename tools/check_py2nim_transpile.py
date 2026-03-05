#!/usr/bin/env python3
"""Compatibility wrapper for check_py2nim_transpile; delegates to check_py2x_transpile.py."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIFIED = ROOT / "tools" / "check_py2x_transpile.py"
TARGET = "nim"


def main() -> int:
    ap = argparse.ArgumentParser(description="compat wrapper: check_py2nim_transpile")
    ap.add_argument("--verbose", action="store_true", help="forward to unified checker")
    args = ap.parse_args()

    cmd = ["python3", str(UNIFIED), "--target", TARGET]
    if args.verbose:
        cmd.append("--verbose")

    cp = subprocess.run(cmd, cwd=ROOT)
    return cp.returncode


if __name__ == "__main__":
    raise SystemExit(main())
