#!/usr/bin/env python3
"""Regenerate src/runtime/east/ from src/pytra runtime sources.

The files under src/runtime/east/ are local generated cache files and are not
committed. This script rebuilds them through pytra-cli parse/resolve/compile/
optimize stages so linker runtime discovery can run from a fresh checkout.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
PYTRA_CLI = ROOT / "src" / "pytra-cli.py"
SOURCE_GROUPS = ("built_in", "std", "utils")


def _runtime_sources() -> list[tuple[str, Path, str]]:
    sources: list[tuple[str, Path, str]] = []
    for group in SOURCE_GROUPS:
        group_root = ROOT / "src" / "pytra" / group
        for source_path in sorted(group_root.rglob("*.py")):
            if source_path.name == "__init__.py":
                continue
            rel_stem = source_path.relative_to(group_root).with_suffix("").as_posix()
            sources.append((group, source_path, rel_stem))
    return sources


def _run_pytra(args: list[str], *, quiet: bool) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, str(PYTRA_CLI)] + args,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    if not quiet:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    return result


def _build_one(group: str, source_path: Path, rel_stem: str, *, quiet: bool) -> int:
    work_root = ROOT / "work" / "tmp" / "runtime-east" / group
    stage_root = work_root / rel_stem
    final_path = ROOT / "src" / "runtime" / "east" / group / (rel_stem + ".east")
    stage_root.mkdir(parents=True, exist_ok=True)
    final_path.parent.mkdir(parents=True, exist_ok=True)

    east1_path = stage_root / (Path(rel_stem).name + ".py.east1")
    east2_path = stage_root / (Path(rel_stem).name + ".east2")
    east3_path = stage_root / (Path(rel_stem).name + ".east3")

    stages = [
        ["-parse", str(source_path), "-o", str(east1_path), "--pretty"],
        ["-resolve", str(east1_path), "-o", str(east2_path), "--pretty"],
        ["-compile", str(east2_path), "-o", str(east3_path), "--pretty"],
        ["-optimize", str(east3_path), "-o", str(final_path), "--pretty"],
    ]
    for stage_args in stages:
        result = _run_pytra(stage_args, quiet=quiet)
        if result.returncode != 0:
            print("FAIL: " + group + "/" + rel_stem + " at " + stage_args[0], file=sys.stderr)
            return result.returncode
    return 0


def regenerate(*, quiet: bool) -> int:
    ok = 0
    fail = 0
    for group, source_path, rel_stem in _runtime_sources():
        label = group + "/" + rel_stem
        if not quiet:
            print("runtime-east: " + label)
        rc = _build_one(group, source_path, rel_stem, quiet=quiet)
        if rc == 0:
            ok += 1
        else:
            fail += 1
    print("runtime-east total: " + str(ok) + " ok, " + str(fail) + " failed")
    return 0 if fail == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate src/runtime/east cache files.")
    parser.add_argument("--quiet", action="store_true", help="suppress per-stage pytra-cli output")
    args = parser.parse_args()
    return regenerate(quiet=bool(args.quiet))


if __name__ == "__main__":
    raise SystemExit(main())
