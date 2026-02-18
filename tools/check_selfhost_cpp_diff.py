#!/usr/bin/env python3
"""Compare py2cpp outputs between Python and selfhost executable."""

from __future__ import annotations

import argparse
import difflib
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2CPP = ROOT / "src" / "py2cpp.py"
DEFAULT_CASES = [
    "test/fixtures/core/add.py",
    "test/fixtures/control/if_else.py",
    "test/fixtures/collections/comprehension_filter.py",
    "sample/py/01_mandelbrot.py",
]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="compare py2cpp outputs: python vs selfhost")
    ap.add_argument("--selfhost-bin", default="selfhost/py2cpp.out")
    ap.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    ap.add_argument("--show-diff", action="store_true")
    args = ap.parse_args()

    selfhost_bin = ROOT / args.selfhost_bin
    if not selfhost_bin.exists():
        print(f"missing selfhost binary: {selfhost_bin}")
        return 2

    mismatches = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        for rel in args.cases:
            src = ROOT / rel
            if not src.exists():
                print(f"missing case: {rel}")
                mismatches += 1
                continue
            out_py = td / (src.stem + ".py.cpp")
            out_sh = td / (src.stem + ".sh.cpp")

            cp1 = _run(["python3", str(PY2CPP), str(src), "-o", str(out_py)])
            if cp1.returncode != 0:
                print(f"[FAIL python] {rel}: {(cp1.stderr.strip() or cp1.stdout.strip()).splitlines()[:1]}")
                mismatches += 1
                continue
            cp2 = _run([str(selfhost_bin), str(src), str(out_sh)])
            if cp2.returncode != 0:
                print(f"[FAIL selfhost] {rel}: {(cp2.stderr.strip() or cp2.stdout.strip()).splitlines()[:1]}")
                mismatches += 1
                continue

            a = out_py.read_text(encoding="utf-8").splitlines()
            b = out_sh.read_text(encoding="utf-8").splitlines()
            if a != b:
                mismatches += 1
                print(f"[DIFF] {rel}")
                if args.show_diff:
                    for ln in difflib.unified_diff(a, b, fromfile=f"{rel}:python", tofile=f"{rel}:selfhost", lineterm=""):
                        print(ln)
            else:
                print(f"[OK] {rel}")

    print(f"mismatches={mismatches}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())

