#!/usr/bin/env python3
"""Ensure regenerated sample outputs have no pending git diff."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_OUTPUT_DIRS = [
    "sample/cpp",
    "sample/rs",
    "sample/cs",
    "sample/js",
    "sample/ts",
    "sample/go",
    "sample/java",
    "sample/swift",
    "sample/kotlin",
]


def main() -> int:
    cmd = ["git", "status", "--porcelain", "--", *SAMPLE_OUTPUT_DIRS]
    cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if cp.returncode != 0:
        msg = cp.stderr.strip() or cp.stdout.strip() or "git status failed"
        print(f"[FAIL] {msg}")
        return 1

    lines = [ln for ln in cp.stdout.splitlines() if ln.strip() != ""]
    if len(lines) == 0:
        print("[OK] sample outputs are clean")
        return 0

    print("[FAIL] sample outputs have uncommitted diffs")
    for ln in lines:
        print(ln)
    print("hint: run tools/run_regen_on_version_bump.py (or regenerate_samples.py) and commit regenerated outputs")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
