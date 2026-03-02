#!/usr/bin/env python3
"""Check py2nim transpile success for smoke fixtures/sample files."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2NIM = ROOT / "src" / "py2nim.py"

CASES = [
    "test/fixtures/core/add.py",
    "test/fixtures/control/if_else.py",
    "test/fixtures/control/for_range.py",
    "test/fixtures/control/range_downcount_len_minus1.py",
    "test/fixtures/oop/inheritance.py",
    "sample/py/01_mandelbrot.py",
]

STAGE2_REMOVED_FRAGMENT = "--east-stage 2 is no longer supported; use EAST3 (default)."


def _run_one(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2NIM), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        runtime_path = out.parent / "py_runtime.nim"
        if not runtime_path.exists():
            return False, "missing runtime file: py_runtime.nim"
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def _run_one_stage2_must_fail(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2NIM), str(src), "--east-stage", "2", "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        return False, "unexpected success for --east-stage 2"
    stderr = cp.stderr.strip()
    if STAGE2_REMOVED_FRAGMENT in stderr:
        return True, ""
    first = stderr.splitlines()[0] if stderr else "missing stderr message"
    return False, "unexpected stage2 error message: " + first


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2nim transpile success for smoke cases")
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    args = ap.parse_args()

    fails: list[tuple[str, str]] = []
    ok = 0
    total = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.nim"
        i = 0
        while i < len(CASES):
            rel = CASES[i]
            src = ROOT / rel
            total += 1
            good, msg = _run_one(src, out)
            if good:
                ok += 1
                if args.verbose:
                    print("OK", rel)
            else:
                fails.append((rel, msg))
            i += 1

        total += 1
        stage2_probe = ROOT / CASES[0]
        good, msg = _run_one_stage2_must_fail(stage2_probe, out)
        if good:
            ok += 1
            if args.verbose:
                print("OK", CASES[0], "[stage2 rejected]")
        else:
            fails.append((CASES[0] + " [stage2 rejected]", msg))

    print(f"checked={total} ok={ok} fail={len(fails)}")
    if fails:
        for rel, msg in fails:
            print(f"FAIL {rel}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
