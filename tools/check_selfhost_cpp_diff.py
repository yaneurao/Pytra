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
    "test/fixtures/core/str_join_method.py",
    "test/fixtures/control/if_else.py",
    "test/fixtures/collections/comprehension_filter.py",
    "test/fixtures/typing/enum_basic.py",
    "test/fixtures/stdlib/enum_extended.py",
    "sample/py/01_mandelbrot.py",
    "sample/py/04_monte_carlo_pi.py",
]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="compare py2cpp outputs: python vs selfhost")
    ap.add_argument("--selfhost-bin", default="selfhost/py2cpp.out")
    ap.add_argument(
        "--selfhost-driver",
        choices=["direct", "bridge"],
        default="direct",
        help="direct: call selfhost bin directly, bridge: use tools/selfhost_transpile.py",
    )
    ap.add_argument("--cases", nargs="*", default=DEFAULT_CASES)
    ap.add_argument("--show-diff", action="store_true")
    ap.add_argument(
        "--mode",
        choices=["strict", "allow-not-implemented"],
        default="allow-not-implemented",
        help="strict: any selfhost failure is mismatch, allow-not-implemented: [not_implemented] is skipped",
    )
    args = ap.parse_args()

    selfhost_bin = ROOT / args.selfhost_bin
    if not selfhost_bin.exists():
        print(f"missing selfhost binary: {selfhost_bin}")
        return 2
    bridge_tool = ROOT / "tools" / "selfhost_transpile.py"
    if args.selfhost_driver == "bridge" and not bridge_tool.exists():
        print(f"missing bridge tool: {bridge_tool}")
        return 2

    mismatches = 0
    skipped = 0
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
            if args.selfhost_driver == "bridge":
                cp2 = _run(
                    [
                        "python3",
                        str(bridge_tool),
                        str(src),
                        "-o",
                        str(out_sh),
                        "--selfhost-bin",
                        str(selfhost_bin),
                    ]
                )
            else:
                cp2 = _run([str(selfhost_bin), str(src), "-o", str(out_sh)])
            if cp2.returncode != 0:
                msg = (cp2.stderr.strip() or cp2.stdout.strip())
                if args.mode == "allow-not-implemented" and "[not_implemented]" in msg:
                    skipped += 1
                    print(f"[SKIP selfhost-not-implemented] {rel}")
                    continue
                if args.mode == "allow-not-implemented" and args.selfhost_driver == "bridge" and "[input_invalid]" in msg:
                    skipped += 1
                    print(f"[SKIP selfhost-bridge-json-unavailable] {rel}")
                    continue
                print(f"[FAIL selfhost] {rel}: {msg.splitlines()[:1]}")
                mismatches += 1
                continue
            if not out_sh.exists():
                print(f"[FAIL selfhost] {rel}: output file was not generated ({out_sh})")
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

    print(f"mismatches={mismatches} skipped={skipped}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
