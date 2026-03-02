#!/usr/bin/env python3
"""Check py2nim transpile success for fixtures and sample files."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2NIM = ROOT / "src" / "py2nim.py"

def _run_one(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2NIM), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(ROOT / "src")}
    )
    if cp.returncode == 0:
        runtime_path = out.parent / "py_runtime.nim"
        if not runtime_path.exists():
            return False, "missing runtime file: py_runtime.nim"
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first

def main() -> int:
    ap = argparse.ArgumentParser(description="check py2nim transpile success for fixtures/sample")
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    args = ap.parse_args()

    fixture_files = sorted((ROOT / "test" / "fixtures" / "nim").glob("*.py"))
    sample_files = sorted((ROOT / "sample" / "py").glob("01_*.py")) # mandelbrot only for now

    fails: list[tuple[str, str]] = []
    total = 0
    ok = 0
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.nim"
        for src in fixture_files + sample_files:
            rel = str(src.relative_to(ROOT))
            total += 1
            good, msg = _run_one(src, out)
            if good:
                ok += 1
                if args.verbose:
                    print(f"OK: {rel}")
            else:
                fails.append((rel, msg))

    print(f"checked={total} ok={ok} fail={len(fails)}")
    if fails:
        for rel, msg in fails:
            print(f"FAIL {rel}: {msg}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
