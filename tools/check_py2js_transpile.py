#!/usr/bin/env python3
"""Compatibility wrapper for check_py2js_transpile; delegates to check_py2x_transpile.py."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIFIED = ROOT / "tools" / "check_py2x_transpile.py"
TARGET = "js"


def main() -> int:
    ap = argparse.ArgumentParser(description="compat wrapper: check_py2js_transpile")
    ap.add_argument("--include-expected-failures", action="store_true", help="forward to unified checker")
    ap.add_argument("--verbose", action="store_true", help="forward to unified checker")
    ap.add_argument("--skip-east3-contract-tests", action="store_true", help="forward to unified checker")
    args = ap.parse_args()

    cmd = ["python3", str(UNIFIED), "--target", TARGET]
    if args.include_expected_failures:
        cmd.append("--include-expected-failures")
    if args.verbose:
        cmd.append("--verbose")
    if args.skip_east3_contract_tests:
        cmd.append("--skip-east3-contract-tests")

    cp = subprocess.run(cmd, cwd=ROOT)
    return cp.returncode


if __name__ == "__main__":
    raise SystemExit(main())
