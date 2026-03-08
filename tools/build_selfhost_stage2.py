#!/usr/bin/env python3
"""Build stage2 selfhost binary (selfhost -> selfhost_selfhost)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_STAGE1 = ROOT / "tools" / "build_selfhost.py"
STAGE1_BIN = ROOT / "selfhost" / "py2cpp.out"
STAGE1_SRC = ROOT / "src" / "py2x-selfhost.py"
STAGE2_CPP = ROOT / "selfhost" / "py2cpp_stage2.cpp"
STAGE2_BIN = ROOT / "selfhost" / "py2cpp_stage2.out"
STAGE1_CPP = ROOT / "selfhost" / "py2cpp.cpp"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from tools.cpp_runtime_deps import collect_runtime_cpp_sources


def _run(cmd: list[str]) -> None:
    cp = subprocess.run(cmd, cwd=str(ROOT), text=True)
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)


def _run_capture(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="build stage2 selfhost transpiler")
    ap.add_argument("--skip-stage1-build", action="store_true", help="skip tools/build_selfhost.py")
    args = ap.parse_args()

    if not args.skip_stage1_build:
        _run(["python3", str(BUILD_STAGE1)])
    if not STAGE1_BIN.exists():
        raise SystemExit("missing stage1 binary: selfhost/py2cpp.out")
    if not STAGE1_SRC.exists():
        raise SystemExit("missing source: src/py2x-selfhost.py")

    stage1_cp = _run_capture([str(STAGE1_BIN), str(STAGE1_SRC), "--target", "cpp", "-o", str(STAGE2_CPP)])
    if stage1_cp.returncode != 0:
        msg = (stage1_cp.stderr or "") + "\n" + (stage1_cp.stdout or "")
        if "[not_implemented]" in msg:
            if not STAGE1_CPP.exists():
                raise SystemExit("missing fallback source: " + str(STAGE1_CPP))
            STAGE2_CPP.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(STAGE1_CPP, STAGE2_CPP)
            print("[WARN] stage1 transpile is not implemented; reused selfhost/py2cpp.cpp for stage2 build")
        else:
            raise SystemExit(stage1_cp.returncode)

    cmd = [
        "g++",
        "-std=c++20",
        "-O2",
        "-Isrc",
        "-Isrc/runtime/cpp",
        str(STAGE2_CPP),
        *[
            str(ROOT / rel_path)
            for rel_path in collect_runtime_cpp_sources([str(STAGE2_CPP)], ROOT / "src")
        ],
        "-o",
        str(STAGE2_BIN),
    ]
    _run(cmd)
    print(str(STAGE2_BIN))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
