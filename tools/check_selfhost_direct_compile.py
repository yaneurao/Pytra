#!/usr/bin/env python3
"""Fast compile check for the direct selfhost .py input route."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELFHOST_BIN = ROOT / "selfhost" / "py2cpp.out"


def _default_cases() -> list[str]:
    return [str(p.relative_to(ROOT)) for p in sorted((ROOT / "sample" / "py").glob("*.py"))]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    py_path = env.get("PYTHONPATH", "")
    src_txt = str(ROOT / "src")
    if py_path == "":
        env["PYTHONPATH"] = src_txt
    elif src_txt not in py_path.split(":"):
        env["PYTHONPATH"] = src_txt + ":" + py_path
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)


def _resolve_selfhost_target(selfhost_bin: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    cp = subprocess.run([str(selfhost_bin), "--help"], cwd=ROOT, capture_output=True, text=True)
    text = (cp.stdout or "") + "\n" + (cp.stderr or "")
    if "--target" in text:
        return "cpp"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="check selfhost direct path transpile + compile (-fsyntax-only)")
    ap.add_argument("--selfhost-bin", default=str(SELFHOST_BIN))
    ap.add_argument("--selfhost-target", default="auto")
    ap.add_argument("--cases", nargs="*", default=_default_cases())
    args = ap.parse_args()

    selfhost_bin = Path(args.selfhost_bin)
    if not selfhost_bin.exists():
        print(f"[FAIL] missing selfhost binary: {selfhost_bin}")
        return 2
    selfhost_target = _resolve_selfhost_target(selfhost_bin, str(args.selfhost_target))

    failures = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        td = Path(tmpdir)
        for rel in args.cases:
            src = ROOT / rel
            if not src.exists():
                print(f"[FAIL missing] {rel}")
                failures += 1
                continue

            out_cpp = td / f"{src.stem}.selfhost.cpp"
            transpile_cmd = [str(selfhost_bin), str(src)]
            if selfhost_target != "":
                transpile_cmd.extend(["--target", selfhost_target])
            transpile_cmd.extend(["-o", str(out_cpp)])
            cp_transpile = _run(transpile_cmd)
            if cp_transpile.returncode != 0:
                msg = cp_transpile.stderr.strip() or cp_transpile.stdout.strip()
                print(f"[FAIL selfhost-transpile] {rel}: {msg.splitlines()[:1]}")
                failures += 1
                continue

            cp_compile = _run(
                [
                    "g++",
                    "-std=c++20",
                    "-fsyntax-only",
                    "-Isrc",
                    "-Isrc/runtime/cpp",
                    str(out_cpp),
                ]
            )
            if cp_compile.returncode != 0:
                msg = cp_compile.stderr.strip() or cp_compile.stdout.strip()
                print(f"[FAIL compile] {rel}: {msg.splitlines()[:1]}")
                failures += 1
                continue

            print(f"[OK] {rel}")

    print(f"failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
