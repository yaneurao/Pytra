#!/usr/bin/env python3
"""Regression bundle for Go/Swift/Kotlin native-backend rollout.

Swift runtime parity is intentionally excluded for now:
- native Swift execution runner (`swiftc`) is not available in this repo setup.
- sidecar runtime parity also cannot be stabilized because runtime JS shim assets
  required by py2js imports are not provisioned in the parity temp workspace.

Swift coverage is enforced via native-default smoke/transpile checks.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=ROOT)
    return cp.returncode


def main() -> int:
    steps: list[list[str]] = [
        ["python3", "-m", "unittest", "discover", "-s", "test/unit", "-p", "test_py2go_smoke.py", "-v"],
        ["python3", "-m", "unittest", "discover", "-s", "test/unit", "-p", "test_py2swift_smoke.py", "-v"],
        ["python3", "-m", "unittest", "discover", "-s", "test/unit", "-p", "test_py2kotlin_smoke.py", "-v"],
        ["python3", "tools/check_py2go_transpile.py"],
        ["python3", "tools/check_py2swift_transpile.py"],
        ["python3", "tools/check_py2kotlin_transpile.py"],
        [
            "python3",
            "tools/runtime_parity_check.py",
            "--case-root",
            "fixture",
            "--targets",
            "go,kotlin",
            "add",
            "if_else",
            "for_range",
            "inheritance",
            "instance_member",
            "super_init",
            "--ignore-unstable-stdout",
            "--kotlin-backend",
            "native",
        ],
        [
            "python3",
            "tools/runtime_parity_check.py",
            "--case-root",
            "sample",
            "--targets",
            "go,kotlin",
            "01_mandelbrot",
            "02_raytrace_spheres",
            "03_julia_set",
            "04_orbit_trap_julia",
            "05_mandelbrot_zoom",
            "06_julia_parameter_sweep",
            "07_game_of_life_loop",
            "08_langtons_ant",
            "09_fire_simulation",
            "--ignore-unstable-stdout",
            "--kotlin-backend",
            "native",
        ],
    ]

    i = 0
    while i < len(steps):
        code = _run(steps[i])
        if code != 0:
            return code
        i += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
