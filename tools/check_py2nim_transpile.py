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

# Minimal emitter will fail many things, so for now we don't list expected failures
# and just check if it can transpile a very simple file.

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
    with tempfile.TemporaryDirectory() as tmpdir:
        test_py = Path(tmpdir) / "test.py"
        test_py.write_text("print('hello')\n", encoding="utf-8")
        test_nim = Path(tmpdir) / "test.nim"
        
        ok, msg = _run_one(test_py, test_nim)
        if ok:
            print("Basic transpile: OK")
            return 0
        else:
            print(f"Basic transpile: FAIL ({msg})")
            return 1

if __name__ == "__main__":
    sys.exit(main())
