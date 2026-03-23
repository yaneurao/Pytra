#!/usr/bin/env python3
"""Build selfhost transpiler C++ binary end-to-end.

Steps:
1) transpile src/pytra-cli.py -> work/selfhost/py2cpp.cpp
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

SELFHOST = ROOT / "work" / "selfhost"
CPP_OUT = SELFHOST / "py2cpp.cpp"
BIN_OUT = SELFHOST / "py2cpp.out"
SELFHOST_ENTRY = ROOT / "src" / "pytra-cli.py"
STAGE_BOUNDARY_GUARD = ROOT / "tools" / "check_east_stage_boundary.py"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(cmd, cwd=str(cwd or ROOT), text=True)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def runtime_cpp_sources() -> list[str]:
    rels = collect_runtime_cpp_sources([str(CPP_OUT)], ROOT / "src")
    return [str(ROOT / rel) for rel in rels]


def build_stage_boundary_guard_cmd(guard_path: Path) -> list[str]:
    return ["python3", str(guard_path)]


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


def build_selfhost_multimod_link_cmd(selfhost_entry: Path, linked_dir: Path) -> list[str]:
    """Stage 1+2: compile + link → linked EAST."""
    return [
        "python3",
        str(ROOT / "src" / "pytra-cli.py"),
        str(selfhost_entry),
        "--target",
        "cpp",
        "--link-only",
        "--output-dir",
        str(linked_dir),
    ]


def build_selfhost_multimod_emit_cmd(link_output: Path, output_dir: Path) -> list[str]:
    """Stage 3: linked EAST → C++ via toolchain/emit/cpp.py."""
    return [
        "python3",
        str(ROOT / "src" / "toolchain" / "emit" / "cpp.py"),
        str(link_output),
        "--output-dir",
        str(output_dir),
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
    multi_module = "--multi-module" in sys.argv
    run(build_stage_boundary_guard_cmd(STAGE_BOUNDARY_GUARD))

    if multi_module:
        multimod_dir = SELFHOST / "cpp"
        build_dir = SELFHOST / "build"
        link_output = build_dir / "manifest.json"
        # Stage 1+2: compile + link (writes manifest.json + east3/ into build_dir)
        run(build_selfhost_multimod_link_cmd(SELFHOST_ENTRY, build_dir))
        # Stage 3: emit C++ (only C++ emitter imported)
        run(build_selfhost_multimod_emit_cmd(link_output, multimod_dir))
        print(f"multi-module output: {multimod_dir}")
        return 0
    else:
        # Existing single-file path
        run(build_selfhost_transpile_cmd(SELFHOST_ENTRY, CPP_OUT))
        cpp_sources = runtime_cpp_sources()
        run(build_selfhost_compile_cmd(CPP_OUT, BIN_OUT, cpp_sources))
        print(str(BIN_OUT))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
