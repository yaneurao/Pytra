#!/usr/bin/env python3
"""Run local CI-equivalent checks in a fixed order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    p = subprocess.run(cmd, cwd=str(ROOT))
    return int(p.returncode)


def main() -> int:
    steps: list[list[str]] = [
        ["python3", "tools/check_transpiler_version_gate.py"],
        ["python3", "tools/check_todo_priority.py"],
        ["python3", "tools/check_runtime_cpp_layout.py"],
        ["python3", "tools/run_regen_on_version_bump.py", "--verify-cpp-on-diff"],
        ["python3", "tools/check_py2cpp_transpile.py"],
        ["python3", "test/unit/test_code_emitter.py"],
        ["python3", "test/unit/test_py2cpp_features.py"],
        ["python3", "tools/build_selfhost.py"],
        [
            "python3",
            "tools/check_selfhost_cpp_diff.py",
            "--mode",
            "allow-not-implemented",
        ],
        [
            "python3",
            "tools/check_selfhost_stage2_cpp_diff.py",
            "--mode",
            "allow-not-implemented",
        ],
    ]
    for step in steps:
        rc = run(step)
        if rc != 0:
            print(f"[FAIL] {' '.join(step)}")
            return rc
    print("[OK] local CI checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
