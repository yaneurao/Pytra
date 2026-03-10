#!/usr/bin/env python3
"""Compare py2cpp outputs between Python and stage2 selfhost binary."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_STAGE2 = ROOT / "tools" / "build_selfhost_stage2.py"
CHECK_DIFF = ROOT / "tools" / "check_selfhost_cpp_diff.py"
STAGE2_BIN = ROOT / "selfhost" / "py2cpp_stage2.out"


def _run(cmd: list[str]) -> int:
    cp = subprocess.run(cmd, cwd=str(ROOT), text=True)
    return cp.returncode


def build_check_diff_cmd(
    selfhost_bin: Path,
    *,
    cases: list[str],
    show_diff: bool,
    mode: str,
) -> list[str]:
    cmd = [
        "python3",
        str(CHECK_DIFF),
        "--selfhost-bin",
        str(selfhost_bin),
        "--selfhost-driver",
        "direct",
        "--mode",
        mode,
    ]
    if show_diff:
        cmd.append("--show-diff")
    if len(cases) > 0:
        cmd.append("--cases")
        cmd.extend(cases)
    return cmd


def main() -> int:
    ap = argparse.ArgumentParser(description="compare outputs: python vs selfhost stage2")
    ap.add_argument("--skip-build", action="store_true", help="skip building stage2 selfhost binary")
    ap.add_argument("--show-diff", action="store_true")
    ap.add_argument("--mode", choices=["strict", "allow-not-implemented"], default="allow-not-implemented")
    ap.add_argument("--cases", nargs="*", default=[])
    args = ap.parse_args()

    if not args.skip_build:
        rc = _run(["python3", str(BUILD_STAGE2)])
        if rc != 0:
            return rc
    if not STAGE2_BIN.exists():
        print(f"missing stage2 binary: {STAGE2_BIN}")
        return 2

    return _run(
        build_check_diff_cmd(
            STAGE2_BIN,
            cases=list(args.cases),
            show_diff=bool(args.show_diff),
            mode=args.mode,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
