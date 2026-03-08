#!/usr/bin/env python3
"""Run full sample parity through the stage2 selfhost binary."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_STAGE2 = ROOT / "tools" / "build_selfhost_stage2.py"
VERIFY_E2E = ROOT / "tools" / "verify_selfhost_end_to_end.py"
STAGE2_BIN = ROOT / "selfhost" / "py2cpp_stage2.out"


def default_sample_cases() -> list[str]:
    return [str(path.relative_to(ROOT)) for path in sorted((ROOT / "sample" / "py").glob("*.py"))]


def build_verify_cmd(selfhost_bin: Path, cases: list[str]) -> list[str]:
    return [
        "python3",
        str(VERIFY_E2E),
        "--skip-build",
        "--selfhost-bin",
        str(selfhost_bin),
        "--cases",
        *cases,
    ]


def _run(cmd: list[str]) -> int:
    cp = subprocess.run(cmd, cwd=str(ROOT), text=True)
    return cp.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="run full sample parity through stage2 selfhost binary")
    ap.add_argument("--skip-build", action="store_true", help="skip tools/build_selfhost_stage2.py")
    ap.add_argument("--selfhost-bin", default=str(STAGE2_BIN), help="path to stage2 selfhost binary")
    ap.add_argument("--cases", nargs="*", default=None, help="override sample cases")
    args = ap.parse_args()

    selfhost_bin = Path(args.selfhost_bin)
    cases = list(args.cases) if args.cases else default_sample_cases()

    if not args.skip_build:
        rc = _run(["python3", str(BUILD_STAGE2)])
        if rc != 0:
            return rc
    if not selfhost_bin.exists():
        print(f"missing stage2 binary: {selfhost_bin}")
        return 2

    return _run(build_verify_cmd(selfhost_bin, cases))


if __name__ == "__main__":
    raise SystemExit(main())
