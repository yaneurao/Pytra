#!/usr/bin/env python3
"""Build selfhost transpiler C++ binary end-to-end.

Steps:
1) prepare selfhost/py2cpp.py from src/py2cpp.py
2) sync src/runtime -> selfhost/runtime
3) transpile selfhost/py2cpp.py -> selfhost/py2cpp.cpp
4) compile with runtime cpp sources
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELFHOST = ROOT / "selfhost"
SRC_RUNTIME = ROOT / "src" / "runtime"
SELFHOST_RUNTIME = SELFHOST / "runtime"
CPP_OUT = SELFHOST / "py2cpp.cpp"
BIN_OUT = SELFHOST / "py2cpp.out"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd or ROOT), text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def runtime_cpp_sources() -> list[str]:
    files = sorted(SELFHOST_RUNTIME.rglob("*.cpp"))
    return [str(p) for p in files]


def main() -> int:
    run(["python3", "tools/prepare_selfhost_source.py"]) 

    SELFHOST_RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC_RUNTIME, SELFHOST_RUNTIME, dirs_exist_ok=True)

    run(["python3", "src/py2cpp.py", "selfhost/py2cpp.py", "-o", str(CPP_OUT)])

    cpp_sources = runtime_cpp_sources()
    cmd = [
        "g++",
        "-std=c++17",
        "-O2",
        "-Iselfhost",
        str(CPP_OUT),
        *cpp_sources,
        "-o",
        str(BIN_OUT),
    ]
    run(cmd)

    print(str(BIN_OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
