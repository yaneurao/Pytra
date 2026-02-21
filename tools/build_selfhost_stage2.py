#!/usr/bin/env python3
"""Build stage2 selfhost binary (selfhost -> selfhost_selfhost)."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_STAGE1 = ROOT / "tools" / "build_selfhost.py"
STAGE1_BIN = ROOT / "selfhost" / "py2cpp.out"
STAGE1_SRC = ROOT / "selfhost" / "py2cpp.py"
STAGE2_CPP = ROOT / "selfhost" / "py2cpp_stage2.cpp"
STAGE2_BIN = ROOT / "selfhost" / "py2cpp_stage2.out"


def _run(cmd: list[str]) -> None:
    cp = subprocess.run(cmd, cwd=str(ROOT), text=True)
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)


def _runtime_cpp_sources() -> list[str]:
    out: list[str] = []
    for p in sorted((ROOT / "src" / "runtime" / "cpp" / "pytra").rglob("*.cpp")):
        out.append(str(p))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="build stage2 selfhost transpiler")
    ap.add_argument("--skip-stage1-build", action="store_true", help="skip tools/build_selfhost.py")
    args = ap.parse_args()

    if not args.skip_stage1_build:
        _run(["python3", str(BUILD_STAGE1)])
    if not STAGE1_BIN.exists():
        raise SystemExit("missing stage1 binary: selfhost/py2cpp.out")
    if not STAGE1_SRC.exists():
        raise SystemExit("missing source: selfhost/py2cpp.py")

    _run([str(STAGE1_BIN), str(STAGE1_SRC), "-o", str(STAGE2_CPP)])

    cmd = [
        "g++",
        "-std=c++20",
        "-O2",
        "-Isrc",
        "-Isrc/runtime/cpp",
        str(STAGE2_CPP),
        *_runtime_cpp_sources(),
        "-o",
        str(STAGE2_BIN),
    ]
    _run(cmd)
    print(str(STAGE2_BIN))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
