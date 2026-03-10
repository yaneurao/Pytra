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


def build_selfhost_transpile_cmd(selfhost_entry: Path, cpp_out: Path) -> list[str]:
    return [
        "python3",
        str(selfhost_entry),
        str(selfhost_entry),
        "--target",
        "cpp",
        "-o",
        str(cpp_out),
    ]


def build_selfhost_compile_cmd(cpp_out: Path, bin_out: Path, cpp_sources: list[str]) -> list[str]:
    return [
        "g++",
        "-std=c++20",
        "-O2",
        "-Isrc",
        "-Isrc/runtime/cpp",
        str(cpp_out),
        *cpp_sources,
        "-o",
        str(bin_out),
    ]

def main() -> int:
    run(build_selfhost_transpile_cmd(SELFHOST_ENTRY, CPP_OUT))

    cpp_sources = runtime_cpp_sources()
    run(build_selfhost_compile_cmd(CPP_OUT, BIN_OUT, cpp_sources))

    print(str(BIN_OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
