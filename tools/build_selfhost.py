#!/usr/bin/env python3
"""Build selfhost transpiler C++ binary end-to-end.

Steps:
1) transpile src/py2x-selfhost.py -> selfhost/py2cpp.cpp
2) compile with src/runtime/cpp sources
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tools.cpp_runtime_deps import collect_runtime_cpp_sources

SELFHOST = ROOT / "selfhost"
CPP_OUT = SELFHOST / "py2cpp.cpp"
BIN_OUT = SELFHOST / "py2cpp.out"
SELFHOST_ENTRY = ROOT / "src" / "py2x-selfhost.py"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd or ROOT), text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def runtime_cpp_sources() -> list[str]:
    rels = collect_runtime_cpp_sources([str(CPP_OUT)], ROOT / "src")
    return [str(ROOT / rel) for rel in rels]

def main() -> int:
    run(
        [
            "python3",
            str(SELFHOST_ENTRY),
            str(SELFHOST_ENTRY),
            "--target",
            "cpp",
            "-o",
            str(CPP_OUT),
        ]
    )

    cpp_sources = runtime_cpp_sources()
    cmd = [
        "g++",
        "-std=c++20",
        "-O2",
        "-Isrc",
        "-Isrc/runtime/cpp",
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
